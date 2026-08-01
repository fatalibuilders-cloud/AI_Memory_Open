import type { Metadata, Viewport } from "next";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Masjid Fund — build a mosque, one donation at a time",
    template: "%s · Masjid Fund",
  },
  description:
    "Fund the construction of masajid around the world. Choose a verified building project, see exactly what your donation pays for, and follow the build to completion.",
  manifest: "/manifest.webmanifest",
  icons: { icon: "/icon.svg" },
  openGraph: {
    title: "Masjid Fund",
    description:
      "Fund the construction of masajid around the world — see exactly what your donation builds.",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#114535",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col bg-sand-50 text-masjid-900 antialiased">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-masjid-800 focus:px-4 focus:py-2 focus:text-white"
        >
          Skip to content
        </a>
        <Header />
        <main id="main" className="flex-1">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
