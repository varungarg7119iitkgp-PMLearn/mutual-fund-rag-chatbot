import type { Metadata } from "next";
import { Poppins } from "next/font/google";
import "./globals.css";

const poppins = Poppins({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "WealthAI — Mutual Fund RAG Assistant",
  description:
    "Dark Wealth Manager AI — a facts-only, RAG-powered mutual fund assistant for 20 curated schemes.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${poppins.className} min-h-screen bg-bg-main text-text-primary`}
      >
        {children}
      </body>
    </html>
  );
}

