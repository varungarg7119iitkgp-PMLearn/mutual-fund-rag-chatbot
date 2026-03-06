"use client";

import { useState } from "react";
import { BarChart3, Compass, Menu, Sparkles, TrendingUp, X } from "lucide-react";
import clsx from "clsx";
import { SidebarNav } from "./SidebarNav";
import { HeaderBar, MobileTicker } from "./HeaderBar";
import { ChatPanel } from "./ChatPanel";
import { MarketPulsePanel } from "./MarketPulsePanel";

const FUND_CATEGORIES = [
  { key: "equity", label: "Equity", color: "bg-accent-growth" },
  { key: "debt", label: "Debt", color: "bg-sky-500" },
  { key: "hybrid", label: "Hybrid", color: "bg-orange-400" },
  { key: "commodities", label: "Commodities", color: "bg-amber-300" },
];

const POPULAR_QUERIES = [
  "Show key stats for HDFC Silver ETF FoF.",
  "What is the expense ratio of DSP Credit Risk Fund?",
  "5-year returns for Invesco India PSU Equity?",
];

export function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [pulseOpen, setPulseOpen] = useState(false);

  return (
    <div className="flex h-[100dvh] w-full overflow-hidden bg-bg-main text-text-primary">
      {/* Desktop sidebar -- unchanged */}
      <SidebarNav />

      <div className="flex min-w-0 flex-1 flex-col lg:border-l lg:border-border-subtle">
        {/* Mobile-only header */}
        <div className="flex items-center justify-between border-b border-border-subtle bg-bg-subtle/70 px-4 py-3 backdrop-blur-md lg:hidden">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-border-subtle text-text-secondary transition hover:border-accent-growth hover:text-text-primary"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-accent-growth/30 to-accent-growth/10">
              <Sparkles className="h-4 w-4 text-accent-growth" />
            </div>
            <span className="text-sm font-semibold tracking-wide">WealthAI</span>
          </div>

          <button
            type="button"
            onClick={() => setPulseOpen(true)}
            className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-border-subtle text-text-secondary transition hover:border-accent-growth hover:text-text-primary"
          >
            <TrendingUp className="h-5 w-5" />
          </button>
        </div>

        {/* Mobile ticker strip */}
        <MobileTicker />

        {/* Desktop header with ticker */}
        <HeaderBar />

        <main className="flex flex-1 overflow-hidden px-2 py-2 sm:px-4 sm:py-4 lg:px-6 lg:py-6">
          <div className="flex min-w-0 flex-1 gap-4">
            <section className="flex min-w-0 flex-1 flex-col overflow-hidden">
              <div className="flex flex-1 flex-col overflow-hidden rounded-2xl border border-border-subtle bg-bg-subtle/80 shadow-card-elevated">
                <ChatPanel />
              </div>
            </section>

            {/* Desktop-only Market Pulse */}
            <aside className="hidden w-[320px] flex-shrink-0 xl:block">
              <div className="flex flex-1 flex-col rounded-2xl border border-border-subtle bg-bg-subtle/80 shadow-card-elevated">
                <MarketPulsePanel />
              </div>
            </aside>
          </div>
        </main>
      </div>

      {/* Mobile Sidebar Drawer */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 w-72 animate-slide-in-left border-r border-border-subtle bg-bg-subtle/95 backdrop-blur-md">
            <div className="flex items-center justify-between px-4 py-4">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-accent-growth/30 to-accent-growth/10 shadow-glow-accent">
                  <Sparkles className="h-4 w-4 text-accent-growth" />
                </div>
                <span className="text-sm font-semibold">WealthAI</span>
              </div>
              <button
                type="button"
                onClick={() => setSidebarOpen(false)}
                className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-text-muted transition hover:text-text-primary"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="overflow-y-auto px-4 pb-6 scrollbar-thin">
              <SidebarDrawerContent />
            </div>
          </div>
        </div>
      )}

      {/* Mobile Market Pulse Drawer */}
      {pulseOpen && (
        <div className="fixed inset-0 z-50 xl:hidden">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setPulseOpen(false)}
          />
          <div className="absolute inset-y-0 right-0 w-80 animate-slide-in-right border-l border-border-subtle bg-bg-subtle/95 backdrop-blur-md">
            <div className="flex items-center justify-between px-4 py-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                <TrendingUp className="h-4 w-4 text-accent-growth" />
                Market Pulse
              </div>
              <button
                type="button"
                onClick={() => setPulseOpen(false)}
                className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-text-muted transition hover:text-text-primary"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="overflow-y-auto pb-6 scrollbar-thin">
              <MarketPulsePanel />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SidebarDrawerContent() {
  return (
    <>
      <div className="mb-6">
        <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
          <Compass className="h-3.5 w-3.5" />
          Categories
        </div>
        <div className="space-y-2">
          {FUND_CATEGORIES.map((cat) => (
            <button
              key={cat.key}
              type="button"
              className={clsx(
                "flex w-full items-center gap-2 rounded-full border border-border-subtle bg-bg-main/60 px-3 py-2 text-xs text-text-secondary transition hover:border-accent-growth hover:text-text-primary"
              )}
            >
              <span className={clsx("inline-flex h-2.5 w-2.5 rounded-full", cat.color)} />
              <span>{cat.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4">
        <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
          <BarChart3 className="h-3.5 w-3.5" />
          Popular Queries
        </div>
        <div className="space-y-2">
          {POPULAR_QUERIES.map((q) => (
            <button
              key={q}
              type="button"
              className="w-full rounded-full border border-border-subtle bg-bg-main/60 px-3 py-2 text-left text-xs text-text-secondary transition hover:border-accent-growth hover:text-text-primary"
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
