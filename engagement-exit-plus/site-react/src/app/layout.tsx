import type { Metadata } from "next";
import "./globals.css";
import { site } from "@/lib/site";
import { SiteBar } from "@/components/site-bar";
import { Sidebar } from "@/components/sidebar";

export const metadata: Metadata = {
  title: `${site.account} · Engagement (internal)`,
  robots: { index: false, follow: false },
  ...(site.brand ? { icons: { icon: site.brand.sf } } : {}),
};

// Runs before first paint so the sidebar opens (or stays hidden) without a jump.
const SB_BOOT = `try{var n=matchMedia("(max-width:960px)").matches,s=localStorage.getItem("eng-sidebar");if(!n&&s!=="closed")document.documentElement.classList.add("sb-open")}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {site.sidebar && <script dangerouslySetInnerHTML={{ __html: SB_BOOT }} />}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" />
      </head>
      <body>
        <SiteBar />
        {site.sidebar && <Sidebar />}
        {children}
      </body>
    </html>
  );
}
