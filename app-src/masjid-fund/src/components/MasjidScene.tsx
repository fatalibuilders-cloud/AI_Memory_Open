/**
 * Decorative masjid skyline used as project artwork. Drawn inline rather than
 * photographed so the site ships without image assets or third-party requests;
 * swap for real site photography when a project provides it.
 */

const GRADIENTS: Record<string, string> = {
  emerald: "from-masjid-800 via-masjid-700 to-masjid-500",
  teal: "from-masjid-900 via-masjid-700 to-teal-600",
  sky: "from-masjid-900 via-sky-800 to-sky-600",
  amber: "from-masjid-800 via-brass-600 to-brass-400",
};

export function MasjidScene({
  accent = "emerald",
  className = "",
}: {
  accent?: string;
  className?: string;
}) {
  const gradient = GRADIENTS[accent] ?? GRADIENTS.emerald;
  return (
    <div className={`relative overflow-hidden bg-gradient-to-br ${gradient} ${className}`}>
      <div className="pattern-stars absolute inset-0 opacity-15" aria-hidden />
      <svg
        viewBox="0 0 300 140"
        preserveAspectRatio="xMidYMax meet"
        className="absolute inset-x-0 bottom-0 h-full w-full"
        aria-hidden
      >
        <g fill="rgba(255,255,255,0.16)">
          <circle cx="232" cy="34" r="13" />
          <path d="M232 34a13 13 0 0 1-9 0" fill="rgba(0,0,0,0.12)" />
        </g>
        <g fill="rgba(255,255,255,0.9)">
          {/* Main dome and hall */}
          <path d="M150 46c16 11 25 23 25 34 0 13-11 22-25 22s-25-9-25-22c0-11 9-23 25-34Z" />
          <rect x="105" y="100" width="90" height="40" rx="4" />
          <path d="M150 40a3 3 0 0 1 3 3c0 2-3 5-3 5s-3-3-3-5a3 3 0 0 1 3-3Z" />
          {/* Flanking minarets */}
          <rect x="88" y="58" width="9" height="82" rx="4.5" />
          <rect x="203" y="58" width="9" height="82" rx="4.5" />
          <circle cx="92.5" cy="53" r="5.5" />
          <circle cx="207.5" cy="53" r="5.5" />
          {/* Side halls */}
          <path d="M62 112c8-9 16-9 24 0v28H62Z" />
          <path d="M214 112c8-9 16-9 24 0v28h-24Z" />
        </g>
        <g fill="rgba(12,50,39,0.55)">
          {/* Arched openings */}
          <path d="M150 118c5 0 9 4 9 9v13h-18v-13c0-5 4-9 9-9Z" />
          <path d="M126 124c3.5 0 6 2.6 6 6v10h-12v-10c0-3.4 2.5-6 6-6Z" />
          <path d="M174 124c3.5 0 6 2.6 6 6v10h-12v-10c0-3.4 2.5-6 6-6Z" />
        </g>
      </svg>
    </div>
  );
}
