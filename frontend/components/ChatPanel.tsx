"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import {
  ArrowUp,
  BarChart3,
  Calculator,
  ExternalLink,
  HelpCircle,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type ChatChunk = {
  chunk_id: string;
  text: string;
  metadata: Record<string, unknown>;
  score: number;
};

type ChatResponse = {
  answer: string;
  used_chunks: ChatChunk[];
  model: string;
};

const WELCOME_CHIPS: { label: string; query: string; icon: typeof BarChart3 }[] = [
  {
    label: "Expense ratio of HDFC Silver ETF FoF",
    query: "What is the expense ratio of HDFC Silver ETF FoF Direct Growth?",
    icon: Calculator,
  },
  {
    label: "5-year returns for Invesco PSU Equity",
    query: "Show me 5-year returns for Invesco India PSU Equity Fund.",
    icon: BarChart3,
  },
  {
    label: "Exit load for HDFC Arbitrage FoF",
    query: "How does the exit load work for HDFC Income Plus Arbitrage Active FoF?",
    icon: HelpCircle,
  },
];

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:8000";

function formatTimestamp(raw: string): string {
  const match = raw.match(
    /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?/
  );
  if (!match) return raw;
  try {
    const d = new Date(match[0] + "Z");
    return d.toLocaleString("en-IN", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  } catch {
    return raw;
  }
}

function humanizeContent(text: string): string {
  return text.replace(
    /Last updated from sources:\s*(\S+)/gi,
    (_full, ts: string) => `Last updated from sources: ${formatTimestamp(ts)}`
  );
}

function extractDomain(url: string): string {
  try {
    const host = new URL(url).hostname.replace(/^www\./, "");
    return host;
  } catch {
    return url;
  }
}

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStartedAt, setLoadingStartedAt] = useState<number | null>(null);
  const [lastChunks, setLastChunks] = useState<ChatChunk[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const hasConversation = messages.length > 0;

  async function sendQuestion(question: string) {
    const trimmed = question.trim();
    if (!trimmed || isLoading) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setLoadingStartedAt(Date.now());
    setLastChunks([]);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: trimmed,
          fund_hint: undefined,
          top_k: 8,
        }),
      });

      if (!res.ok) {
        const detail = await res.text();
        throw new Error(detail || `HTTP ${res.status}`);
      }

      const data = (await res.json()) as ChatResponse;
      setLastChunks(data.used_chunks ?? []);

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content:
          "I am fully tired now, can we discuss this tomorrow? Will get some sleep. 😴",
      };
      setMessages((prev) => [...prev, assistantMessage]);
      console.error(err);
    } finally {
      setIsLoading(false);
      setLoadingStartedAt(null);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void sendQuestion(input);
  }

  function onTextareaKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendQuestion(input);
    }
  }

  function handleSendClick() {
    void sendQuestion(input);
  }

  return (
    <div className="flex min-w-0 flex-1 flex-col">
      <div className="flex-1 overflow-y-auto px-3 py-6 scrollbar-thin sm:px-4 sm:py-8 lg:px-12">
        <div className="mx-auto w-full space-y-6 lg:max-w-3xl">
          {!hasConversation ? (
            <WelcomeState onChipClick={(q) => void sendQuestion(q)} />
          ) : (
            <Conversation messages={messages} isLoading={isLoading} loadingStartedAt={loadingStartedAt} />
          )}

          {lastChunks.length > 0 && (
            <div className="rounded-xl border border-border-subtle bg-bg-main/60 px-3 py-3 text-xs text-text-secondary sm:px-4 lg:mx-auto lg:max-w-3xl">
              <div className="mb-2 font-semibold text-text-primary">
                Sources referenced
              </div>
              <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin">
                {extractDistinctSources(lastChunks).map((src) => (
                  <a
                    key={src}
                    href={src}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex flex-shrink-0 items-center gap-1.5 rounded-full border border-border-subtle bg-bg-main/70 px-3 py-1.5 text-[11px] text-accent-neutral transition hover:border-accent-growth hover:text-text-primary"
                  >
                    <ExternalLink className="h-3 w-3 flex-shrink-0" />
                    {extractDomain(src)}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <form
        onSubmit={onSubmit}
        className="bg-transparent px-3 pb-3 pt-0 sm:px-4 sm:pb-4 lg:px-8"
      >
        <div className="mx-auto flex w-full items-end gap-2 rounded-2xl bg-bg-main/80 px-3 py-2 shadow-card-elevated lg:max-w-3xl">
          <div className="relative flex-1">
            <textarea
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onTextareaKeyDown}
              placeholder="Ask about any of our 20 curated mutual funds…"
              ref={textareaRef}
              className="w-full max-w-full resize-none rounded-2xl border border-border-subtle bg-transparent px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-growth focus:outline-none focus:ring-2 focus:ring-accent-growth/40"
            />
          </div>
          <button
            type="button"
            onClick={handleSendClick}
            disabled={isLoading || !input.trim()}
            className="inline-flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-accent-growth text-bg-main shadow transition hover:scale-105 active:scale-95 disabled:opacity-60"
          >
            <ArrowUp className="h-4 w-4" />
          </button>
        </div>
        <p className="mx-auto mt-2 w-full text-center text-[11px] text-text-muted lg:max-w-3xl">
          Facts-only assistant. No investment advice provided.
        </p>
      </form>
    </div>
  );
}

function WelcomeState({ onChipClick }: { onChipClick: (q: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      <div className="mb-6 flex flex-col items-center gap-3 sm:mb-8 sm:gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-accent-growth/40 to-accent-growth/10 shadow-glow-accent sm:h-14 sm:w-14">
          <Sparkles className="h-6 w-6 text-accent-growth sm:h-7 sm:w-7" />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-balance sm:text-xl md:text-2xl">
            Welcome, Investor.
          </h1>
          <p className="mt-2 max-w-md text-xs leading-relaxed text-text-secondary sm:mt-3 sm:text-sm">
            I am your factual Wealth Assistant. I provide data-grounded insights
            on 20 curated mutual funds, powered by a Gemini-based RAG backend.
          </p>
        </div>
      </div>

      <div className="mt-2 flex w-full max-w-lg flex-col gap-2 px-2 sm:flex-row sm:flex-wrap sm:justify-center sm:gap-3 sm:px-0">
        {WELCOME_CHIPS.map((chip) => {
          const Icon = chip.icon;
          return (
            <button
              key={chip.query}
              type="button"
              onClick={() => onChipClick(chip.query)}
              className="inline-flex items-center gap-2 rounded-full border border-border-subtle bg-bg-main/80 px-4 py-3 text-xs text-text-secondary transition hover:scale-[1.02] hover:border-accent-growth hover:text-text-primary active:scale-[0.98] sm:py-2.5"
            >
              <Icon className="h-3.5 w-3.5 flex-shrink-0 text-accent-neutral" />
              {chip.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Conversation({
  messages,
  isLoading,
  loadingStartedAt,
}: {
  messages: ChatMessage[];
  isLoading: boolean;
  loadingStartedAt: number | null;
}) {
  return (
    <div className="mx-auto flex flex-col gap-4 lg:max-w-3xl">
      {messages.map((m) =>
        m.role === "user" ? (
          <div key={m.id} className="flex justify-end animate-fade-up">
            <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-accent-growth/15 px-4 py-3 text-sm leading-relaxed text-text-primary sm:max-w-[75%]">
              {m.content}
            </div>
          </div>
        ) : (
          <div key={m.id} className="flex justify-start animate-fade-up">
            <div className="max-w-[95%] rounded-2xl rounded-tl-sm border border-border-subtle bg-bg-main/80 px-3 py-3 text-sm sm:max-w-[85%] sm:px-4">
              <div className="mb-2 flex items-center gap-2 text-xs text-text-secondary">
                <span className="font-semibold text-text-primary">
                  WealthAI
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-bg-subtle px-2 py-0.5 text-[10px] text-accent-growth">
                  <ShieldCheck className="h-3 w-3" />
                  Verified
                </span>
              </div>
              <div className="whitespace-pre-wrap leading-relaxed text-text-primary">
                {humanizeContent(m.content)}
              </div>
            </div>
          </div>
        )
      )}
      {isLoading && <LoadingIndicator startedAt={loadingStartedAt} />}
    </div>
  );
}

function LoadingIndicator({ startedAt }: { startedAt: number | null }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!startedAt) return;
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [startedAt]);

  let statusText = "Thanks for your query, let me think…";
  if (elapsed >= 20) {
    statusText = "Almost there, wrapping up my analysis…";
  } else if (elapsed >= 10) {
    statusText = "Your query just got me thinking a little deeper, bear with me…";
  }

  return (
    <div className="flex justify-start animate-fade-up">
      <div className="flex flex-col gap-1.5 rounded-2xl rounded-tl-sm border border-border-subtle bg-bg-main/60 px-4 py-3 text-xs text-text-muted">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent-neutral" />
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent-neutral [animation-delay:150ms]" />
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent-neutral [animation-delay:300ms]" />
          </div>
          <span>{statusText}</span>
        </div>
        {elapsed >= 5 && (
          <span className="text-[10px] text-text-muted/70">
            {elapsed}s elapsed
          </span>
        )}
      </div>
    </div>
  );
}

function extractDistinctSources(chunks: ChatChunk[]): string[] {
  const urls = new Set<string>();
  for (const c of chunks) {
    const meta = c.metadata ?? {};
    const raw = (meta as any).source_urls ?? (meta as any).source_url ?? [];
    if (typeof raw === "string") {
      urls.add(raw);
    } else if (Array.isArray(raw)) {
      for (const u of raw) {
        if (typeof u === "string") urls.add(u);
      }
    }
  }
  return Array.from(urls);
}
