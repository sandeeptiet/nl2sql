"use client";

import { useState, useRef, useEffect } from "react";
import { UserBubble, BotBubble, LoadingSkeleton } from "./components/MessageBubble";
import ChatInput from "./components/ChatInput";
import SuggestedQueries from "./components/SuggestedQueries";
import { Message, ChatMessage, QueryResponse } from "./lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const HISTORY_WINDOW = 6;

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function buildHistory(msgs: Message[]): ChatMessage[] {
    const history: ChatMessage[] = [];
    for (const m of msgs) {
      if (m.type === "user") {
        history.push({ role: "user", content: m.content });
      } else {
        history.push({ role: "assistant", content: m.response.nl_summary });
      }
    }
    return history.slice(-HISTORY_WINDOW);
  }

  async function handleSend(question: string) {
    const userMsg: Message = { type: "user", content: question };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          chat_history: buildHistory(updatedMessages),
        }),
      });

      const data: QueryResponse = await res.json();
      setMessages((prev) => [...prev, { type: "bot", response: data }]);
    } catch {
      const errorResponse: QueryResponse = {
        nl_summary: "Failed to reach the backend. Is it running?",
        table: [],
        columns: [],
        sql: "",
        query_type: "error",
        row_count: 0,
        latency_ms: 0,
        chart_type: null,
        error: "Network error",
      };
      setMessages((prev) => [...prev, { type: "bot", response: errorResponse }]);
    } finally {
      setLoading(false);
    }
  }

  const showSuggestions = messages.length === 0 && !loading;

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-gray-950">
      {/* Header */}
      <header className="flex-shrink-0 border-b border-gray-200 dark:border-gray-800 px-4 py-3">
        <h1 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
          nl2sql <span className="font-normal text-gray-400">— Ask your data anything</span>
        </h1>
      </header>

      {/* Chat area */}
      <main className="flex-1 overflow-y-auto px-4 py-4 max-w-3xl w-full mx-auto">
        {showSuggestions && (
          <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
            <div>
              <p className="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-1">
                What do you want to know?
              </p>
              <p className="text-sm text-gray-400">
                Ask a question in plain English — SQL is generated automatically.
              </p>
            </div>
            <SuggestedQueries onSelect={handleSend} />
          </div>
        )}

        {messages.map((msg, i) =>
          msg.type === "user" ? (
            <UserBubble key={i} content={msg.content} />
          ) : (
            <BotBubble key={i} response={msg.response} />
          )
        )}

        {loading && <LoadingSkeleton />}
        <div ref={bottomRef} />
      </main>

      {/* Input */}
      <footer className="flex-shrink-0 border-t border-gray-200 dark:border-gray-800 px-4 py-3 max-w-3xl w-full mx-auto">
        {!showSuggestions && (
          <div className="mb-2">
            <SuggestedQueries onSelect={handleSend} />
          </div>
        )}
        <ChatInput onSend={handleSend} disabled={loading} />
      </footer>
    </div>
  );
}
