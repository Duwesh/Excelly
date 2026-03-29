"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { ChatMessage } from "@/components/ChatMessage";
import { FileUpload } from "@/components/FileUpload";
import { ArtifactsPanel } from "@/components/ArtifactsPanel";
import { StreamingIndicator } from "@/components/StreamingIndicator";
import { ThemeToggle } from "@/components/ThemeToggle";
import {
  streamAnalysis,
  type UploadResult,
  type Artifact,
  type StreamEvent,
} from "@/lib/api";
import { Send, Paperclip, X, Sparkles, Plus, FileSpreadsheet } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  nodeName?: string;
  reasoningSteps?: string[];
}

const SUGGESTIONS = [
  "Summarize this dataset",
  "Show key statistics",
  "Find trends and patterns",
  "Detect outliers or anomalies",
];

export function ChatPage() {
  // ── State ────────────────────────────────────────────────────────────────
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentNode, setCurrentNode] = useState<string | null>(null);
  const [reasoningSteps, setReasoningSteps] = useState<string[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [uploadedFile, setUploadedFile] = useState<UploadResult | null>(null);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const isEmpty = messages.length === 0;

  // ── Effects ───────────────────────────────────────────────────────────────
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isStreaming, currentNode]);

  useEffect(() => {
    if (!inputRef.current) return;
    inputRef.current.style.height = "auto";
    inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 150)}px`;
  }, [input]);

  // ── Helpers ───────────────────────────────────────────────────────────────
  const resetStreamingState = () => {
    setIsStreaming(false);
    setCurrentNode(null);
    setReasoningSteps([]);
  };

  const pushMessage = (msg: Message) => setMessages((prev) => [...prev, msg]);


  const handleSend = useCallback(async () => {
    const query = input.trim();
    if (!query || isStreaming) return;

    setInput("");
    setError(null);
    setShowFileUpload(false);
    setArtifacts([]);

    pushMessage({ id: crypto.randomUUID(), role: "user", content: query });
    setIsStreaming(true);

    const backendQuery = uploadedFile ? `[Uploaded file: ${uploadedFile.filename}]\n${query}` : query;

    // Inline handlers so useCallback deps are satisfied without listing createStreamHandlers
    let latestNode = "";
    const steps: string[] = [];
    const addStep = (text: string) => { if (!steps.includes(text)) { steps.push(text); setReasoningSteps([...steps]); } };
    const reset = () => { setIsStreaming(false); setCurrentNode(null); setReasoningSteps([]); };

    const onEvent = (event: StreamEvent) => {
      if (event.status === "completed") return;
      if (event.error) { setError(event.error); return; }
      if (event.thread_id) setThreadId(event.thread_id);
      if (event.node) { latestNode = event.node; setCurrentNode(event.node); }
      if (event.update?.route_decision?.reasoning) addStep(event.update.route_decision.reasoning);
      if (event.update?.supervisor_decision?.reasoning) addStep(event.update.supervisor_decision.reasoning);
      if (event.update?.analysis_plan) addStep(`Plan:\n${event.update.analysis_plan}`);
      if (event.update?.messages && ["chat", "followup_answer"].includes(latestNode) && !event.is_subgraph) {
        event.update.messages.forEach((msg) => {
          if (msg.content && msg.type !== "HumanMessage") {
            setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "assistant", content: msg.content, nodeName: latestNode }]);
          }
        });
      }
      if (event.update?.final_analysis && !event.is_subgraph) {
        const content = event.update.final_analysis as string;
        setMessages((prev) => prev.some((m) => m.content === content) ? prev : [...prev, { id: crypto.randomUUID(), role: "assistant", content, nodeName: "finalizer", reasoningSteps: [...steps] }]);
      }
      if (event.update?.artifacts) setArtifacts((prev) => [...prev, ...(event.update!.artifacts as Artifact[])]);
    };

    abortRef.current = await streamAnalysis(
      backendQuery,
      uploadedFile?.file_path || null,
      threadId,
      onEvent,
      reset,
      (err: string) => { setError(err); reset(); },
    );
  }, [input, isStreaming, uploadedFile, threadId]);

  const handleStop = () => { abortRef.current?.abort(); resetStreamingState(); };

  const handleNewChat = () => {
    setMessages([]);
    setArtifacts([]);
    setError(null);
    setThreadId(null);
    setUploadedFile(null);
    setInput("");
    setShowFileUpload(false);
    resetStreamingState();
  };

  const handleSuggestion = (text: string) => {
    setInput(text);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  // ── UI ────────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-screen bg-background">

      {/* ── Header ── */}
      <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto max-w-4xl flex items-center justify-between px-6 py-3">
          {/* Brand */}
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-primary/10 border border-primary/20">
              <FileSpreadsheet className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-foreground leading-none">Excelly</h1>
              <p className="text-[11px] text-muted-foreground leading-none mt-0.5">Excel Analysis Agent</p>
            </div>
          </div>

          {/* Right controls */}
          <div className="flex items-center gap-2">
            {uploadedFile && (
              <div className="hidden sm:flex items-center gap-1.5 text-xs text-emerald-500 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-1.5 rounded-full border border-emerald-500/20">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="truncate max-w-[140px] font-medium">{uploadedFile.filename}</span>
              </div>
            )}
            {!isEmpty && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleNewChat}
                disabled={isStreaming}
                className="gap-1.5 h-8 text-xs rounded-lg border-border/50"
              >
                <Plus className="h-3.5 w-3.5" />
                New Chat
              </Button>
            )}
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* ── Chat area ── */}
      <div className="flex-1 overflow-hidden">
        <div ref={scrollRef} className="h-full overflow-y-auto scroll-smooth">
          <div className="mx-auto max-w-4xl">

            {isEmpty ? (
              /* ── Empty / welcome state ── */
              <div className="flex flex-col items-center justify-center min-h-[calc(100vh-180px)] px-6 py-12">
                <div className="flex flex-col items-center gap-8 max-w-lg w-full text-center">

                  {/* Icon */}
                  <div className="relative group">
                    <div className="absolute -inset-6 bg-primary/10 blur-2xl rounded-full opacity-60 group-hover:opacity-100 transition-opacity duration-500" />
                    <div className="relative flex items-center justify-center h-20 w-20 rounded-2xl bg-linear-to-br from-background to-muted border border-primary/20 shadow-lg">
                      <Sparkles className="h-9 w-9 text-primary" />
                    </div>
                  </div>

                  {/* Title */}
                  <div className="space-y-2">
                    <h2 className="text-3xl font-bold tracking-tight bg-linear-to-br from-foreground to-foreground/60 bg-clip-text text-transparent">
                      Excelly
                    </h2>
                    <p className="text-sm text-muted-foreground leading-relaxed max-w-xs mx-auto">
                      Upload a spreadsheet and ask questions in plain English. I&apos;ll generate insights, charts, and analysis.
                    </p>
                  </div>

                  {/* File upload */}
                  <div className="w-full">
                    <FileUpload
                      onFileUploaded={setUploadedFile}
                      onFileRemoved={() => setUploadedFile(null)}
                      uploadedFile={uploadedFile}
                      disabled={isStreaming}
                    />
                  </div>

                  {/* Suggestion chips — shown after file is ready */}
                  {uploadedFile && (
                    <div className="flex flex-wrap gap-2 justify-center animate-in fade-in slide-in-from-bottom-2 duration-300">
                      {SUGGESTIONS.map((s) => (
                        <button
                          key={s}
                          onClick={() => handleSuggestion(s)}
                          className="px-3.5 py-1.5 text-xs font-medium rounded-full bg-muted border border-border/60 hover:border-primary/40 text-muted-foreground hover:text-foreground transition-all duration-200 hover:shadow-sm"
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* ── Message list ── */
              <div className="py-6 px-4">
                {messages.map((msg) => (
                  <ChatMessage
                    key={msg.id}
                    role={msg.role}
                    content={msg.content}
                    nodeName={msg.nodeName}
                    reasoningSteps={msg.reasoningSteps}
                  />
                ))}

                {isStreaming && (
                  <StreamingIndicator currentNode={currentNode} reasoningSteps={reasoningSteps} />
                )}

                {error && (
                  <div className="my-3 mx-4 rounded-xl bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
                    {error}
                  </div>
                )}

                {!isStreaming && artifacts.length > 0 && (
                  <ArtifactsPanel artifacts={artifacts} />
                )}

                <div className="h-4" />
              </div>
            )}

          </div>
        </div>
      </div>

      {/* ── Inline file upload panel (when in chat) ── */}
      {showFileUpload && !isEmpty && (
        <div className="mx-auto max-w-4xl w-full px-6">
          <div className="mb-2 animate-in fade-in slide-in-from-bottom-2 duration-200">
            <FileUpload
              onFileUploaded={(r) => { setUploadedFile(r); setShowFileUpload(false); }}
              onFileRemoved={() => setUploadedFile(null)}
              uploadedFile={uploadedFile}
              disabled={isStreaming}
            />
          </div>
        </div>
      )}

      {/* ── Sticky file badge while chatting ── */}
      {!isEmpty && uploadedFile && !showFileUpload && (
        <div className="mx-auto max-w-4xl w-full px-6">
          <div className="mb-1">
            <FileUpload
              onFileUploaded={setUploadedFile}
              onFileRemoved={() => setUploadedFile(null)}
              uploadedFile={uploadedFile}
              disabled={isStreaming}
            />
          </div>
        </div>
      )}

      {/* ── Input bar ── */}
      <div className="sticky bottom-0 border-t border-border/40 bg-background/90 backdrop-blur-xl">
        <div className="mx-auto max-w-4xl px-6 py-3">
          <div className="flex items-end gap-2">

            {/* Attach file */}
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0 h-10 w-10 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/50"
              onClick={() => setShowFileUpload((v) => !v)}
              disabled={isStreaming}
              title="Attach file"
            >
              <Paperclip className="h-4.5 w-4.5" />
            </Button>

            {/* Textarea */}
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder={uploadedFile ? "Ask about your data…" : "Upload a file or ask a question…"}
                rows={1}
                disabled={isStreaming}
                autoComplete="off"
                suppressHydrationWarning
                className="w-full resize-none overflow-hidden rounded-xl border border-border/50 bg-muted/30 px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/40 transition-all duration-200 disabled:opacity-50"
              />
            </div>

            {/* Send / Stop */}
            {isStreaming ? (
              <Button
                variant="destructive"
                size="icon"
                className="shrink-0 h-10 w-10 rounded-xl"
                onClick={handleStop}
                title="Stop"
              >
                <X className="h-4 w-4" />
              </Button>
            ) : (
              <Button
                size="icon"
                className="shrink-0 h-10 w-10 rounded-xl bg-primary hover:bg-primary/90 transition-colors shadow-sm"
                onClick={handleSend}
                disabled={!input.trim()}
                title="Send"
              >
                <Send className="h-4 w-4" />
              </Button>
            )}
          </div>

          <p className="text-[10px] text-muted-foreground/40 text-center mt-2">
            AI-generated analysis may contain errors. Verify important results independently.
          </p>
        </div>
      </div>

    </div>
  );
}
