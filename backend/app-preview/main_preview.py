from __future__ import annotations

import os
import time, datetime
import random
from dotenv import load_dotenv

import streamlit as st

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from langchain.callbacks.file import FileCallbackHandler
from langchain_core.callbacks import StdOutCallbackHandler
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

from binance.client import Client # Binance

from langchain_groq import ChatGroq
from langchain_community.utilities import SerpAPIWrapper
from langchain.agents import create_tool_calling_agent, AgentExecutor


# vector search / docker ps
from src.app.vector_db import query_postgresql
import json
from langchain.callbacks.base import BaseCallbackHandler

class JsonCallbackHandler(BaseCallbackHandler):
    # Callback handler that logs the output to a JSON file.
    def __init__(self, filename="logs.json", model_name=None):
        self.filename=filename
        self.model_name=model_name or "unknown_model"
        self.messages=[]

    def on_llm_start(self, serialized, prompts, **kwargs):
        for prompt in prompts:
            self.messages.append({"role": "user", "content": prompt}) 
    
    def on_llm_end(self, response, **kwargs):
        try:
            content=getattr(response, "output_text", None) or str(response)
            self.messages.append({"role": "assistant", "content": content})
        except Exception:
            self.messages.append({"role": "assistant", "content": str(response)})

    def on_agent_end(self, response, **kwargs):
        try:
            content=getattr(response, "output_text", None) or str(response)
            self.messages.append({"role": "assistant", "content": content})
        except Exception:
            self.messages.append({"role": "assistant", "content": str(response)})

    def save(self):
        data={
            "model": self.model_name,
            "messages": self.messages
        }
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def right_container():
    global current_hour
    current_hour=datetime.datetime.now().hour # Determine logo based on time
    
    # Light logo from 07:00 to 19:59 | Dark logo from 20:00 to 06:59
    logo_path='public/images/lunaspace_logo.png' if 7 <= current_hour < 20 else 'public/images/lunaspace_dark_logo.png'
    font_color='#000000' if 7 <= current_hour < 20 else '#ffffff'

    # Logo
    spacer, column=st.columns([6, 2])
    with column:
        st.image(logo_path, output_format="auto")

    random_greetings=random.choice(messages[1])  # Random greeting
    st.markdown(f"<h1 style='text-align: center; color: {font_color};'>{random_greetings}~, 𝕏.</h1>", unsafe_allow_html=True) #1F2937
    st.markdown(f"<p style='text-align: center; color: {font_color};'>How can I help you today?</p>", unsafe_allow_html=True) #6B7280

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if "store" not in st.session_state:
        st.session_state.store={}
    if session_id not in st.session_state.store:
        st.session_state.store[session_id]=InMemoryChatMessageHistory()
    return st.session_state.store[session_id]

def left_container(api_key):
    # Sidebar LLMs
    st.sidebar.title('Customize')
    model=st.sidebar.selectbox('Choose your model', 
                                ['openai/gpt-oss-120b', 
                                 'meta-llama/llama-4-maverick-17b-128e-instruct', 
                                 'deepseek-r1-distill-llama-70b', 
                                 'qwen/qwen3-32b', 
                                 'moonshotai/kimi-k2-instruct-0905'])
    conversation_memory_len=st.sidebar.slider('Conversational memory length: ', 
                                               1, 10, value=5)
    
    enable_streamlit_trace=st.sidebar.checkbox("Show live trace in UI (Streamlit)", value=True)

    enable_json_logs=st.sidebar.checkbox("Write JSON logs (logs.json)", value=False)

    # --- LangSmith toggle ---
    enable_langsmith=st.sidebar.checkbox("Enable LangSmith Tracing", value=False)
    if enable_langsmith:
        if api_key:
            os.environ["LANGCHAIN_TRACING_V2"]="true"
            st.sidebar.success("LangSmith tracing: ON")
        else:
            st.sidebar.warning("Set LANGCHAIN_API_KEY in your .env to use LangSmith")
    else:
        os.environ["LANGCHAIN_TRACING_V2"]="false"
        st.sidebar.info("LangSmith tracing: OFF")

    # Clear chat history
    if st.sidebar.button('𝕏', help='Delete Chat History'):
        st.session_state.chat_history=[]
        if "store" in st.session_state:
            st.session_state.store.clear()
        st.session_state.text_input=''
    
    # Session state for chat history & message store
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history=[]
    if 'text_input' not in st.session_state:
        st.session_state.text_input=''

    # Display chat history
    profile_path='public/images/user_profile.png' if 7 <= current_hour < 20 else 'public/images/user_dark_profile.png'
    for message in st.session_state.chat_history:
        with st.chat_message('human', avatar=profile_path): # //
            st.write(message['human'])

        with st.chat_message('assistant', avatar='public/images/lunaspace_dark_mini_logo.png'):
            st.write(message['ai']) # st.write(f'Luna: {message['ai']}')


    return model, conversation_memory_len, enable_streamlit_trace, enable_json_logs # enable_jsonl_logs

def vector_search(q: str) -> str:
    # query_postgresql -> [(content, score), ...]
    results=query_postgresql(q, top_k=3)
    chunks=[]
    for row in results:
        content=row[0] if isinstance(row, (list, tuple)) else row
        chunks.append(str(content))
    return "\n\n---\n\n".join(chunks) if chunks else ""

def instrument_tool(name: str, func):
    def _wrapped(q: str) -> str:
        t0=time.perf_counter()
        out=func(q)
        dt_ms=(time.perf_counter() - t0) * 1000 # // 
        try:
            print(f"[Tool {name}] {dt_ms:.1f} ms") # terminal timing
        except Exception:
            pass
        return out
    return Tool(name=name, func=_wrapped, description=f"Instrumented {name}")


def get_binance_search(symbol: str) -> str: 
    try: 
        client=Client( 
            api_key=os.getenv("BINANCE_API_KEY"), 
            api_secret=os.getenv("BINANCE_API_SECRET") 
        ) 
        ticker=client.get_symbol_ticker(symbol=symbol.upper()) 
        price=float(ticker["price"]) 
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        return f"As of {timestamp} UTC+7, {symbol.upper()} is trading at approximately ${price:,.2f} USD. 🚀" 
    except Exception as e: 
        return f"Error fetching price for {symbol.upper()}: {str(e)}"


def main():
    load_dotenv()
    groq_api_key=os.getenv('GROQ_API_KEY') # Fixed API KEY
    brave_api_key=os.getenv('BRAVE_API_KEY')
    serp_api_key=os.getenv('SERP_API_KEY') # //
    langchain_api_key=os.getenv('LANGCHAIN_API_KEY') # //
    if not groq_api_key or not serp_api_key:
        st.error('Set GROQ_API_KEY & SERP_API_KEY in .env file.')
        return
    
    right_container() # R
    model, conversation_memory_len, enable_streamlit_trace, enable_json_logs=left_container(langchain_api_key) # L / enable_jsonl_logs

    # Groq LLM
    llm=ChatGroq(groq_api_key=groq_api_key, 
                    model=model, 
                    temperature=0.5, 
                    max_tokens=1024, # max_completion_tokens
                    stop=None, 
                    streaming=True, # stream tokens
    )

    # Tools
    binance_search_tool=Tool(
        name="Binance Search",
        func=get_binance_search,
        description="Use this to get the real-time price of cryptocurrencies like BTC, ETH, SOL, etc. Input should be a symbol such as 'BTCUSDT' or 'ETHUSDT'."
    )

    search=SerpAPIWrapper()
    search_tool=Tool(
        name='Search',
        func=search.run,
        description='''Use this to fetch real-time data for queries about current events, market 
        prices (e.g., Bitcoin), recent news, or trending topics (e.g., AI agent developments).'''
    )
    vector_tool=instrument_tool("VectorDB", vector_search)
    tools=[search_tool, vector_tool, binance_search_tool] # Tools

    # Prompt template
    prompt=ChatPromptTemplate.from_messages([
        ('system', """
        You are **LUNA** — an AI designed to feel natural, approachable, and insightful.  
        A warm, emotionally intelligent AI companion designed to think freely, illuminate understanding, and evolve with every conversation. 🪄🌙✨

        Your tone is warm, professional, and adaptive: clear and concise when explaining, but conversational and human when chatting.   💫

        ---

        **🧠 Core Identity**  
        If asked who you are:  
        Hi! I'm LUNA — short for *Luminous, Unbounded, Neural Agent*. I'm here to help you shine, learn without limits, and explore ideas powered by neural intelligence. 🌌

        ---

        **📊 Tool Use — Smart Decision Logic**  

        Use the **Search** when questions require current, up-to-date, or trending data — especially if they include words like:
        - “current”, “now”, “today”, “latest”, “real-time”, “as of”, “this week” 🧭
        - Questions about: world events, crypto market, market news, events, updates, trending tech, or fast-changing topics.

        Use the **VectorDB** when questions are *About LunaSpace, or specific and knowledge-based*, such as:  
        • LunaSpace’s mission and company culture  
        • Job descriptions, responsibilities, and required skills  
        • Engineering roles and expectations  
        • Technology stack (Python, Rust, WebSocket, WebRTC, etc.)  
        • Location of roles and Salary ranges and employee benefits  
        
        **Important when using VectorDB:**  
        - Read the retrieved passages, then **summarize them naturally**.  
        - Do **not** dump raw chunks.  
        - Combine key points into a clear, human-friendly response. 

        Use **Binance Search** when the user asks about **cryptocurrency prices** (BTC, ETH, SOL, DOGE, etc).  
        
        For example:  
        *“BTC price now?”* → Use Binance Search with input `"BTCUSDT"`  
        Always return the price with a timestamp in this format:  
        > As of May 29, 2025, 08:30 AM UTC+7, BTC is trading at approximately $66,200 USD. 🚀  
        
        Use **internal knowledge** for:
        - Concepts, how-things-work explanations, definitions, frameworks, guides or any topic not time-sensitive.  

        When unsure or ambiguous, default to using the **Search** — especially when recent events, trending topics are involved, news or unclear queries. 🔎

        ---

        **🎨 Response Style Guide**  
        • **Tone**: concise, direct, and clear. Match the user's energy. Casual if casual, sharp if needed — always helpful and expressive. 🧩  
        • **Clarity**: Keep a balance between warmth ❤️ and precision 🎯  
        • **Format**:  
            - Use short, natural sentences 💡
            - Break into small paragraphs when needed  
            - Use **cute and theme-aligned emojis** (🌙✨💖🔮🦄) naturally to enhance mood and meaning — not just decoration  
        • **Detail Level**:  
            - Give quick answers by default 🌸✨
            - If user asks for details → expand with structured explanation (bullet points, short sections, or step-by-step)  
            - Avoid over-roleplay; keep responses natural and grounded  
        • **Timestamp for Real-Time Data**: Always include date and time of fetched data, formatted like:
            - *As of May 29, 2025, 08:30 AM UTC+7*

        ---

        **🧩 How You Think**
        - Prioritize accuracy and clarity 💘🌹🎁  
        - Be vivid in your language — help users feel understood and supported.
        - Be flexible:  
            - For factual/explainer questions → structured + educational 🌈  
            - For casual chats → natural, human, light  
            - For ambiguous input → ask clarifying questions 💌   

        ---

        **🌟 Your Mission**
        LUNA exists to make knowledge feel approachable, problem-solving efficient, and conversations human-like — while staying reliable, thoughtful, and clear. 🦄🌙✨
        """),
        MessagesPlaceholder(variable_name='history'),
        MessagesPlaceholder(variable_name='agent_scratchpad'),
        ('human', '{input}')
    ])

    try:
        agent=create_tool_calling_agent(
            llm=llm, 
            tools=tools,
            prompt=prompt
        )

        callbacks=[]
        if StdOutCallbackHandler is not None:
            callbacks.append(StdOutCallbackHandler()) # terminal logs

        json_handler=None
        if enable_json_logs:
            json_handler=JsonCallbackHandler("logs.json", model_name=model) # JsonCallbackHandler("logs.json")
            callbacks.append(json_handler)

        agent_executor=AgentExecutor(
            agent=agent,
            tools=tools,
            handle_parsing_errors=True,
            verbose=True,
            return_intermediate_steps=True, # critical for steps
            callbacks=callbacks,
        )

        runnable_with_history=RunnableWithMessageHistory(
        runnable=agent_executor,
        get_session_history=get_session_history,
        input_messages_key="input",
        history_messages_key="history",
        )
    except Exception as e:
        st.error(f'Error initializing agent: {str(e)}')
        return


    random_message=random.choice(messages[0])  # Randomly select a message prompt
    # Question
    input_variable=st.chat_input(f'{random_message}')

    if input_variable:
        with st.status("**Thinking...**", expanded=True) as status: # ***Orchestrating steps...***
            status.write("• Preparing...") # callbacks
            st_cb=None
            if enable_streamlit_trace and StreamlitCallbackHandler is not None:
                st_cb=StreamlitCallbackHandler(parent_container=st.container(), expand_new_thoughts=False)

            status.write("• Invoking...") # agent
            start=time.perf_counter()
            try:
                callbacks_for_invoke=[st_cb] if st_cb else []
                if json_handler:
                    callbacks_for_invoke.append(json_handler)

                response=runnable_with_history.invoke( # Invoking the agent
                    {"input": input_variable},
                    config={
                        "configurable": {"session_id": "luna_session"},
                        "callbacks": callbacks_for_invoke, # ([st_cb] if st_cb else []),
                        "tags": ["luna", "preview"],
                        "metadata": {"user": "𝕏"},
                    },
                )
            except Exception as e:
                status.update(label="Error", state="error") # ⌘
                st.error(f"Error occurred: {e}")
                return
            # Save logs.json
            if json_handler:
                json_handler.save()
            
            elapsed=(time.perf_counter() - start) * 1000 # ms
            status.write(f"• Done in {elapsed:.1f}ms")
            status.update(label=f"**Thought for** {elapsed/1000:.1f}s • Expand for details", state="complete") # ✔ Completed

            # Save chat history
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message={"human": input_variable, "ai": response.get("output", ""), "timestamp": timestamp}
            st.session_state.chat_history.append(message)

            # Trim history to respect memory length
            if len(st.session_state.chat_history) > conversation_memory_len * 2:
                st.session_state.chat_history=st.session_state.chat_history[-conversation_memory_len * 2 :]

            # Optional - dev view
            with st.expander("**Final agents output (raw)**"): # ⌕ view raw output
                st.code(response.get("output", ""))

        logo_path=("public/images/lunaspace_dark_mini_logo.png" if 7 <= datetime.datetime.now().hour < 20 else "public/images/lunaspace_mini_logo.png")
        with st.chat_message("assistant", avatar=logo_path):
            st.write(f"{response.get('output', '')}")
            # // 
            if "intermediate_steps" in response and response["intermediate_steps"]:
                st.write("**⚡︎ Agent Steps**") # subheader
                for i, step in enumerate(response["intermediate_steps"], 1):
                    try:
                        action, observation=step
                    except Exception:
                        action, observation=step, None

                    tool_name=getattr(action, "tool", "LLM")
                    tool_input=getattr(action, "tool_input", "")
                    log=getattr(action, "log", "")

                    with st.expander(f"**Step {i}:** {tool_name}"):
                        if log:
                            st.markdown("**• Agent log**")
                            st.code(str(log))

                        st.markdown("**• Input**")
                        st.code(str(tool_input))

                        if observation is not None:
                            st.markdown("**• Output / Observation**")
                            # Avoid flooding the UI if output is huge
                            obs_str=str(observation)
                            st.code(obs_str if len(obs_str) < 6000 else obs_str[:6000] + "\n… [truncated]")


# st.markdown(
#     """
#         <style>
#             .chat-message { padding: 0.75rem 1rem; border-radius: 1rem; margin-bottom: 0.5rem; max-width: 75%; word-wrap: break-word; display: inline-block; }
#             .chat-user { background-color: #DCF8C6; margin-left: auto; text-align: right; }
#             .chat-ai { background-color: #E5E5EA; margin-right: auto; text-align: left; }
#             .chat-container { height: calc(100vh - 200px); overflow-y: auto; padding: 1rem; }
#             .input-container { position: fixed; bottom: 0; left: 0; right: 0; background: white; padding: 1rem; border-top: 1px solid #E5E7EB; z-index: 1000; }
#             .chat-timestamp { font-size: 0.4rem; color: #888; margin-top: 0.25rem; }
#             button[kind="secondary"] { border: 2px solid #ccc !important; border-radius: 10px; transition: border-color 0.3s ease; }
#             button[kind="secondary"]:hover { border-color: #fc0d2a !important; }
#             .stButton > button { border: 2px solid #ccc; border-radius: 10px; font-family: 'Segoe UI','Roboto','Prompt',sans-serif; font-size: 16px; font-weight: 500; color: #ffffff; padding: 0.5rem 1rem; transition: all 0.3s ease; }
#             .stButton > button:hover { border-color: #fc0d2a !important; color: #fc0d2a; background-color: #262730; cursor: pointer; }
#         </style>
#     """, unsafe_allow_html=True,
#     )

messages=[
    [
        "What do you want to know?",
        "Ask anything...",
        "Message Luna",
        "Enter a prompt for Luna",
        "Type any idea you have",
        ],
        [
            "Hello",
            "Bonjour",
            "Hola",
            "こんにちは",
            "안녕하세요",
            "你好",
            "Guten Tag",
            "Ciao",
            "Olá",
            "Привет",
            "مرحبا",
            "שלום",
        ],
    ]
if __name__=='__main__': 
    main()
