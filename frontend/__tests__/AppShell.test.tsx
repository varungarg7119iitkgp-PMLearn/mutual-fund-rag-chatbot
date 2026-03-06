import { render, screen } from "@testing-library/react";
import { AppShell } from "@/components/AppShell";

describe("AppShell", () => {
  it("renders core layout sections", () => {
    render(<AppShell />);

    // Sidebar content
    expect(
      screen.getByText(/WealthAI/i)
    ).toBeInTheDocument();

    // Market Pulse heading
    expect(
      screen.getByText(/Market Pulse/i)
    ).toBeInTheDocument();

    // Chat welcome title
    expect(
      screen.getByText(/Welcome, Investor\./i)
    ).toBeInTheDocument();
  });
});

