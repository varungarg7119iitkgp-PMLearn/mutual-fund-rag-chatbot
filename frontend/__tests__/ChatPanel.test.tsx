import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ChatPanel } from "@/components/ChatPanel";

describe("ChatPanel", () => {
  beforeEach(() => {
    // Mock fetch for /chat
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        answer:
          "This is a test answer.\n\nLast updated from sources: 2026-03-04T00:00:00Z",
        used_chunks: [],
        model: "gemini-3-flash-preview",
      }),
    } as any);
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("shows welcome state and sends a question", async () => {
    render(<ChatPanel />);

    // Welcome heading
    expect(
      screen.getByText(/Welcome, Investor\./i)
    ).toBeInTheDocument();

    const textarea = screen.getByPlaceholderText(
      /Ask me about any of our 20 curated mutual funds/i
    ) as HTMLTextAreaElement;

    fireEvent.change(textarea, {
      target: { value: "Give me an overview of HDFC Silver ETF FoF." },
    });

    const sendButton = screen.getByRole("button");
    fireEvent.click(sendButton);

    // User message appears
    expect(
      await screen.findByText(/Give me an overview of HDFC Silver ETF FoF\./i)
    ).toBeInTheDocument();

    // Assistant answer appears
    await waitFor(() =>
      expect(
        screen.getByText(/This is a test answer\./i)
      ).toBeInTheDocument()
    );

    // Footer line is present
    expect(
      screen.getByText(/Last updated from sources:/i)
    ).toBeInTheDocument();
  });
});

