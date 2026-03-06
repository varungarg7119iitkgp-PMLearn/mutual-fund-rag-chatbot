import { SidebarNav } from "./SidebarNav";
import { HeaderBar } from "./HeaderBar";
import { ChatPanel } from "./ChatPanel";
import { MarketPulsePanel } from "./MarketPulsePanel";

export function AppShell() {
  return (
    <div className="flex h-[100dvh] w-full overflow-hidden bg-bg-main text-text-primary">
      <SidebarNav />

      <div className="flex min-w-0 flex-1 flex-col border-l border-border-subtle">
        <HeaderBar />

        <main className="flex flex-1 overflow-hidden px-4 py-4 lg:px-6 lg:py-6">
          <div className="flex min-w-0 flex-1 gap-4">
            <section className="flex min-w-0 flex-1 flex-col overflow-hidden">
              <div className="flex flex-1 flex-col overflow-hidden rounded-2xl border border-border-subtle bg-bg-subtle/80 shadow-card-elevated">
                <ChatPanel />
              </div>
            </section>

            <aside className="hidden w-[320px] flex-shrink-0 xl:block">
              <div className="flex flex-1 flex-col rounded-2xl border border-border-subtle bg-bg-subtle/80 shadow-card-elevated">
                <MarketPulsePanel />
              </div>
            </aside>
          </div>
        </main>
      </div>
    </div>
  );
}

