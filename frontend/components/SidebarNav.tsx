import { BarChart3, Compass, Sparkles } from "lucide-react";
import clsx from "clsx";

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

export function SidebarNav() {
  return (
    <aside className="hidden w-64 flex-col border-r border-border-subtle bg-bg-subtle/80 px-4 py-6 backdrop-blur-md lg:flex">
      <div className="mb-8 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-accent-growth/30 to-accent-growth/10 shadow-glow-accent">
          <Sparkles className="h-5 w-5 text-accent-growth" />
        </div>
        <div>
          <div className="text-sm font-semibold tracking-wide text-text-primary">
            WealthAI
          </div>
          <div className="text-xs text-text-muted">
            Facts-only Mutual Fund Concierge
          </div>
        </div>
      </div>

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
                "flex w-full items-center gap-2 rounded-full border border-border-subtle bg-bg-main/60 px-3 py-2 text-xs text-text-secondary transition hover:border-accent-growth hover:text-text-primary hover:scale-[1.02]"
              )}
            >
              <span
                className={clsx(
                  "inline-flex h-2.5 w-2.5 rounded-full",
                  cat.color
                )}
              />
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
              className="w-full rounded-full border border-border-subtle bg-bg-main/60 px-3 py-2 text-left text-xs text-text-secondary transition hover:border-accent-growth hover:text-text-primary hover:scale-[1.02]"
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}

