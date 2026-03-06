"use client";

import { Search } from "lucide-react";

const TICKER_ITEMS = [
  { name: "HDFC Silver FoF", nav: "₹43.79", change: "+1.2%" },
  { name: "Nippon Silver FoF", nav: "₹42.28", change: "-0.4%" },
  { name: "ICICI Silver FoF", nav: "₹40.72", change: "+0.6%" },
  { name: "Axis Silver FoF", nav: "₹45.57", change: "+0.9%" },
  { name: "ABSL Silver FoF", nav: "₹41.39", change: "+0.3%" },
];

function getChangeColor(change: string) {
  if (change.startsWith("+")) return "text-accent-growth";
  if (change.startsWith("-")) return "text-danger";
  return "text-accent-neutral";
}

export function HeaderBar() {
  return (
    <header className="border-b border-border-subtle bg-bg-subtle/70 backdrop-blur-md">
      <div className="flex items-center gap-4 px-4 py-3 lg:px-6">
        <div className="hidden min-w-0 flex-1 overflow-hidden rounded-full border border-border-subtle bg-bg-main lg:block">
          <div className="flex max-w-full flex-1 animate-[ticker_60s_linear_infinite] whitespace-nowrap overflow-hidden">
            {Array.from({ length: 2 }).map((_, loopIdx) =>
              TICKER_ITEMS.map((item, idx) => (
                <div
                  key={`${loopIdx}-${idx}`}
                  className="flex min-w-[220px] items-center justify-between border-r border-border-subtle/50 px-5 py-1.5 text-xs text-text-secondary"
                >
                  <span className="font-medium text-text-primary">
                    {item.name}
                  </span>
                  <span className="flex items-center gap-3">
                    <span>{item.nav}</span>
                    <span
                      className={`${getChangeColor(
                        item.change
                      )} animate-ticker-pulse`}
                    >
                      {item.change}
                    </span>
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="flex flex-1 items-center justify-end gap-3">
          <div className="relative w-full max-w-sm">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search within 20 curated mutual funds…"
              className="w-full rounded-full border border-border-subtle bg-bg-main/80 py-2 pl-9 pr-3 text-xs text-text-primary placeholder:text-text-muted focus:border-accent-growth focus:outline-none"
            />
          </div>
        </div>
      </div>

      <style jsx global>{`
        @keyframes ticker {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }
      `}</style>
    </header>
  );
}

