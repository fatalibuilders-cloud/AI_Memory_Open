import Link from "next/link";

// `wide` items are dropped on narrow screens, where the bar has room for the
// short links and the donate button only.
const NAV = [
  { href: "/projects", label: "Projects", wide: false },
  { href: "/about", label: "How it works", wide: true },
  { href: "/faq", label: "FAQ", wide: false },
];

export function Header() {
  return (
    <header className="sticky top-0 z-20 border-b border-sand-200 bg-sand-50/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4">
        <Link href="/" className="flex items-center gap-2.5">
          <MasjidMark />
          <span className="font-display text-lg font-semibold tracking-tight text-masjid-900">
            Masjid Fund
          </span>
        </Link>

        <nav className="flex items-center gap-1 text-sm sm:gap-4">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-2 py-1.5 text-masjid-800/80 hover:text-masjid-900 ${
                item.wide ? "hidden sm:block" : ""
              }`}
            >
              {item.label}
            </Link>
          ))}
          <Link
            href="/donate"
            className="rounded-lg bg-masjid-700 px-4 py-2 font-semibold text-white shadow-sm transition hover:bg-masjid-800"
          >
            Donate
          </Link>
        </nav>
      </div>
    </header>
  );
}

/** Dome-and-minaret mark, drawn inline so there is no image request. */
function MasjidMark() {
  return (
    <svg viewBox="0 0 32 32" className="h-8 w-8" role="img" aria-label="">
      <rect width="32" height="32" rx="8" className="fill-masjid-800" />
      <g className="fill-brass-400">
        <path d="M16 8c2.9 1.9 4.6 4.2 4.6 6.6 0 2.6-2.1 4.4-4.6 4.4s-4.6-1.8-4.6-4.4C11.4 12.2 13.1 9.9 16 8Z" />
        <rect x="8.4" y="19" width="15.2" height="5.4" rx="1.1" />
        <rect x="6" y="12.6" width="1.8" height="11.8" rx="0.9" />
        <rect x="24.2" y="12.6" width="1.8" height="11.8" rx="0.9" />
        <circle cx="6.9" cy="11.2" r="1.2" />
        <circle cx="25.1" cy="11.2" r="1.2" />
        <circle cx="16" cy="6.2" r="1.1" />
      </g>
    </svg>
  );
}
