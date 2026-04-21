import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { UiProvider } from "@/components/ui/providers";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "UnderwriteAI",
  description:
    "AI-powered health insurance underwriting for the Rwandan market",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <UiProvider>{children}</UiProvider>
      </body>
    </html>
  );
}
