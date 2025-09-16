from sentence_transformers import SentenceTransformer
import psycopg2, json

def connect_to_db():
        conn = psycopg2.connect(
            dbname="pgql",
            user="executive", # admin
            password="LunaSp@ceX",
            host="localhost",
            port="5432"
        )
        cur=conn.cursor()
        # cur.execute('''
        #     create table if not exists documents (
        #         id serial primary key auto_increment,
        #         content text,
        #         embedding vector(1024)
        #     );
        # ''')
        # create extension vector;
        # select * from pg_catalog.pg_extension where extname='vector';
        # conn.commit()
        # cur.close()
        # conn.close()
        return conn, cur

def embedding_model():
    model=SentenceTransformer('Snowflake/snowflake-arctic-embed-l-v2.0')
    # content='Introducing a Revolutionary Platform for Tech Startup Creation and Investments.'
    # embedding=model.encode(content).tolist()
    # print(embedding)
    # print(len(embedding))
    return model

def insert_to_db(content):
    embedding=model.encode(content).tolist()
    cur=conn.cursor()
    cur.execute('''
        insert into documents (content, embedding)
        values (%s, %s);
    ''', (content, embedding))
    conn.commit()
    cur.close()

def add_docs(docs):
    for doc in docs:
        insert_to_db(doc)

# Querying the database for similar documents
def query_postgresql(query, top_k=3):
    cur=conn.cursor()
    query_embedding=model.encode(query).tolist() # query_embedding=json.dumps(model.encode(query).tolist())
    cur.execute('''
        select content, embedding <=> %s::vector as similarity_score
        from documents
        order by similarity_score asc
        limit %s;
    ''', (query_embedding, top_k))
    results=cur.fetchall()
    cur.close()
    # conn.close()
    return [r[0] for r in results] # results

conn, cur=connect_to_db()
model=embedding_model()
# add_docs(docs)
