"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, ExternalLink, CheckCircle, XCircle } from "lucide-react";

interface CompoundResponse {
  message: string;
  should_use_compound: boolean;
  detected_urls: string[];
  response: string;
  model: string;
}

interface UrlAnalysisResponse {
  url: string;
  question?: string;
  analysis: string;
  model: string;
}

export default function TestCompoundModelPage() {
  const [message, setMessage] = useState("");
  const [testUrl, setTestUrl] = useState("https://groq.com/blog/inside-the-lpu-deconstructing-groq-speed");
  const [question, setQuestion] = useState("");
  const [primaryModel, setPrimaryModel] = useState("openai/gpt-oss-120b");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<CompoundResponse | null>(null);
  const [urlAnalysis, setUrlAnalysis] = useState<UrlAnalysisResponse | null>(null);
  const [hybridResponse, setHybridResponse] = useState<unknown>(null);
  const [status, setStatus] = useState<{
    available: boolean;
    model: string;
    timeout: number;
    max_retries: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const checkStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const res = await fetch("/api/v1/external/groq-compound/status");
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      
      const data = await res.json();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to check status");
    } finally {
      setLoading(false);
    }
  };

  const testHybridApproach = async () => {
    if (!message.trim()) return;
    
    try {
      setLoading(true);
      setError(null);
      setHybridResponse(null);
      
      const params = new URLSearchParams({
        message: message.trim(),
        primary_model: primaryModel
      });
      
      const res = await fetch(`/api/v1/external/groq-compound/hybrid-chat?${params}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        }
      });
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      
      const data = await res.json();
      setHybridResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process hybrid request");
    } finally {
      setLoading(false);
    }
  };

  const testChatWithUrls = async () => {
    if (!message.trim()) return;
    
    try {
      setLoading(true);
      setError(null);
      setResponse(null);
      
      const params = new URLSearchParams({
        message: message.trim()
      });
      
      const res = await fetch(`/api/v1/external/groq-compound/chat-with-urls?${params}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        }
      });
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      
      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process message");
    } finally {
      setLoading(false);
    }
  };

  const analyzeUrl = async () => {
    if (!testUrl.trim()) return;
    
    try {
      setLoading(true);
      setError(null);
      setUrlAnalysis(null);
      
      const params = new URLSearchParams({
        url: testUrl.trim(),
        ...(question.trim() && { question: question.trim() })
      });
      
      const res = await fetch(`/api/v1/external/groq-compound/analyze-url?${params}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        }
      });
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      
      const data = await res.json();
      setUrlAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze URL");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Groq Compound Model Test</h1>
        <p className="text-muted-foreground">
          Test the Groq compound model functionality for URL-based queries and website analysis.
        </p>
      </div>

      {/* Status Check */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Service Status
            {status?.available ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : status !== null ? (
              <XCircle className="h-5 w-5 text-red-500" />
            ) : null}
          </CardTitle>
          <CardDescription>
            Check if the Groq compound model service is available
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={checkStatus} disabled={loading} className="mb-4">
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            Check Status
          </Button>
          
          {status && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant={status.available ? "default" : "destructive"}>
                  {status.available ? "Available" : "Unavailable"}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Model: {status.model}
                </span>
              </div>
              <div className="text-sm text-muted-foreground">
                Timeout: {status.timeout}s | Max Retries: {status.max_retries}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Hybrid Approach */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Hybrid Approach (Recommended)</CardTitle>
          <CardDescription>
            Use Groq compound for website data + Your chosen AI model for response
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            placeholder="Enter a message with URLs (e.g., 'What are the key points in this article: https://groq.com/blog/...')"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={3}
          />
          
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium">Primary AI Model:</label>
            <select 
              value={primaryModel} 
              onChange={(e) => setPrimaryModel(e.target.value)}
              className="border rounded px-3 py-1"
            >
              <option value="openai/gpt-oss-120b">GPT OSS 120B (Default)</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
              <option value="llama-3.1-70b-versatile">Llama 3.1 70B</option>
            </select>
          </div>
          
          <Button onClick={testHybridApproach} disabled={loading || !message.trim()}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            Test Hybrid Approach
          </Button>
          
          {hybridResponse && (
            <div className="space-y-4 p-4 bg-muted rounded-lg">
              <div className="flex items-center gap-2">
                <Badge variant="default">
                  Hybrid Approach
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Primary: {hybridResponse.metadata?.primary_model}
                </span>
                {hybridResponse.metadata?.used_compound_for_data && (
                  <Badge variant="outline">+ Groq Compound</Badge>
                )}
              </div>
              
              {hybridResponse.metadata?.urls_detected?.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">URLs Analyzed:</h4>
                  <ul className="space-y-1">
                    {hybridResponse.metadata.urls_detected.map((url: string, index: number) => (
                      <li key={index} className="flex items-center gap-2 text-sm">
                        <ExternalLink className="h-3 w-3" />
                        <a href={url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                          {url}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {hybridResponse.metadata?.processing_steps?.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Processing Steps:</h4>
                  <ul className="space-y-1">
                    {hybridResponse.metadata.processing_steps.map((step: string, index: number) => (
                      <li key={index} className="text-sm">
                        • {step.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div>
                <h4 className="font-semibold mb-2">Final Response:</h4>
                <div className="whitespace-pre-wrap text-sm bg-background p-3 rounded border">
                  {hybridResponse.response}
                </div>
              </div>
            </div>
          )}

          {response && (
            <div className="space-y-4 p-4 bg-muted rounded-lg">
              <div className="flex items-center gap-2">
                <Badge variant={response.should_use_compound ? "default" : "secondary"}>
                  {response.should_use_compound ? "Compound Model Used" : "Regular Model"}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Model: {response.model}
                </span>
                {response.note && (
                  <Badge variant="outline">Legacy</Badge>
                )}
              </div>
              
              {response.detected_urls.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Detected URLs:</h4>
                  <ul className="space-y-1">
                    {response.detected_urls.map((url, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm">
                        <ExternalLink className="h-3 w-3" />
                        <a href={url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                          {url}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div>
                <h4 className="font-semibold mb-2">Response:</h4>
                <div className="whitespace-pre-wrap text-sm bg-background p-3 rounded border">
                  {response.response}
                </div>
              </div>
              
              {response.note && (
                <div className="text-sm text-muted-foreground p-2 bg-yellow-50 rounded border">
                  💡 {response.note}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Legacy Chat with URLs */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Legacy: Direct Compound Model</CardTitle>
          <CardDescription>
            Test direct compound model usage (not recommended for production)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            placeholder="Enter a message with URLs for legacy testing"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={2}
          />
          
          <Button onClick={testChatWithUrls} disabled={loading || !message.trim()} variant="outline">
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            Test Legacy Approach
          </Button>
        </CardContent>
      </Card>

      {/* URL Analysis */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Direct URL Analysis</CardTitle>
          <CardDescription>
            Analyze a specific URL with an optional question
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            placeholder="Enter URL to analyze"
            value={testUrl}
            onChange={(e) => setTestUrl(e.target.value)}
          />
          
          <Input
            placeholder="Optional: Ask a specific question about the URL"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          
          <Button onClick={analyzeUrl} disabled={loading || !testUrl.trim()}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            Analyze URL
          </Button>
          
          {urlAnalysis && (
            <div className="space-y-4 p-4 bg-muted rounded-lg">
              <div className="flex items-center gap-2">
                <ExternalLink className="h-4 w-4" />
                <a href={urlAnalysis.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                  {urlAnalysis.url}
                </a>
                <Badge variant="outline">{urlAnalysis.model}</Badge>
              </div>
              
              {urlAnalysis.question && (
                <div>
                  <h4 className="font-semibold mb-2">Question:</h4>
                  <p className="text-sm bg-background p-3 rounded border">
                    {urlAnalysis.question}
                  </p>
                </div>
              )}
              
              <div>
                <h4 className="font-semibold mb-2">Analysis:</h4>
                <div className="whitespace-pre-wrap text-sm bg-background p-3 rounded border">
                  {urlAnalysis.analysis}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-600">
              <XCircle className="h-4 w-4" />
              <span className="font-semibold">Error:</span>
            </div>
            <p className="text-red-600 mt-1">{error}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}