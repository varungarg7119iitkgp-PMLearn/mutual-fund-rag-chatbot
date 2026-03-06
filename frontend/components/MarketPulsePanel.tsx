import { TrendingUp } from "lucide-react";

const MOCK_TRENDING = [
  {
    name: "HDFC Silver ETF FoF Direct Growth",
    category: "Commodities",
    label: "Highly Searched",
  },
  {
    name: "ICICI Prudential PSU Equity Fund Direct Growth",
    category: "Equity",
    label: "On the Radar",
  },
  {
    name: "DSP Credit Risk Fund Direct Plan Growth",
    category: "Debt",
    label: "Stable Interest",
  },
];

export function MarketPulsePanel() {
  return (
    <div className="flex h-full flex-col px-4 py-4">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
          <TrendingUp className="h-4 w-4 text-accent-growth" />
          <span>Market Pulse</span>
        </div>
        <span className="text-[11px] text-text-muted">Anonymized query trends</span>
      </div>

      <div className="space-y-3">
        {MOCK_TRENDING.map((fund) => (
          <button
            key={fund.name}
            type="button"
            className="w-full rounded-xl border border-border-subtle bg-bg-main/60 px-3 py-2 text-left text-xs text-text-secondary transition hover:border-accent-growth hover:text-text-primary"
          >
            <div className="mb-1 text-[11px] font-semibold text-text-primary">
              {fund.name}
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="inline-flex items-center rounded-full bg-bg-subtle px-2 py-0.5 text-[10px] text-accent-neutral">
                {fund.category}
              </span>
              <span className="text-[10px] text-accent-growth">
                {fund.label}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

