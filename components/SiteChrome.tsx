import Link from "next/link";
import styles from "@/app/dashboard.module.css";

export type DashboardPage =
  | "overview"
  | "same-function"
  | "functions"
  | "nir-hir"
  | "hir-ghidra"
  | "variants"
  | "measurement"
  | "quality"
  | "speed"
  | "parity"
  | "releases";

const NAV: {
  id: DashboardPage;
  href: string;
  label: string;
  blurb: string;
}[] = [
  {
    id: "overview",
    href: "/",
    label: "Overview",
    blurb: "Semantic ranking",
  },
  {
    id: "same-function",
    href: "/same-function",
    label: "Same-function",
    blurb: "Boundary honesty",
  },
  {
    id: "functions",
    href: "/functions",
    label: "Functions",
    blurb: "Code grid",
  },
  {
    id: "nir-hir",
    href: "/nir-vs-hir",
    label: "NIR vs HIR",
    blurb: "Source · dual layer",
  },
  {
    id: "hir-ghidra",
    href: "/hir-vs-ghidra",
    label: "HIR vs Ghidra",
    blurb: "Readability · side by side",
  },
  {
    id: "variants",
    href: "/variants",
    label: "Variants",
    blurb: "Compiler × opt",
  },
  {
    id: "measurement",
    href: "/measurement",
    label: "Measurement",
    blurb: "Scope · health",
  },
  {
    id: "quality",
    href: "/quality",
    label: "Quality EXT",
    blurb: "Bare-compile · readability",
  },
  {
    id: "speed",
    href: "/speed",
    label: "Speed",
    blurb: "Decompile latency",
  },
  {
    id: "parity",
    href: "/fission-vs-ghidra",
    label: "Fission ↔ Ghidra",
    blurb: "Shared IR",
  },
  {
    id: "releases",
    href: "/releases",
    label: "Releases",
    blurb: "Trend · what changed",
  },
];

export function SiteChrome({
  active,
  children,
  subtitle,
}: {
  active: DashboardPage;
  children: React.ReactNode;
  subtitle?: string;
}) {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.headerLeft}>
            <Link href="/" className={styles.logo}>
              <span className={styles.logoIcon}>⚡</span>
              <span className={styles.logoText}>Fission</span>
              <span className={styles.logoBadge}>Benchmark</span>
            </Link>
            {subtitle ? <p className={styles.headerSub}>{subtitle}</p> : null}
          </div>
          <nav className={styles.nav} aria-label="Primary">
            {NAV.map((item) => (
              <Link
                key={item.id}
                href={item.href}
                className={
                  active === item.id ? styles.navLinkActive : styles.navLink
                }
                aria-current={active === item.id ? "page" : undefined}
              >
                <span className={styles.navLabel}>{item.label}</span>
                <span className={styles.navBlurb}>{item.blurb}</span>
              </Link>
            ))}
            <a
              href="https://github.com/fission-systems/fission-benchmark"
              target="_blank"
              rel="noopener noreferrer"
              className={styles.headerLink}
            >
              GitHub →
            </a>
          </nav>
        </div>
      </header>
      <main className={styles.main}>{children}</main>
      <footer className={styles.footer}>
        <span>
          Fission Benchmark · Overview · Functions · Measurement · Quality EXT ·
          Speed · IR parity · ISR 15 min
        </span>
        <a
          href="https://github.com/fission-systems/fission-benchmark"
          target="_blank"
          rel="noopener noreferrer"
        >
          fission-systems/fission-benchmark
        </a>
      </footer>
    </div>
  );
}
