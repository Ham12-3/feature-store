import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Suspense } from "react";
import Sidebar from "@/components/Sidebar";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Feature Catalog",
  description: "Browse, search, and discover ML features",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 text-slate-900`}>
        <Suspense>
          <Sidebar />
        </Suspense>
        <main className="ml-64 min-h-screen">{children}</main>
      </body>
    </html>
  );
}
