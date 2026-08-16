import type { NextConfig } from "next";

/**
 * Response headers applied to every route.
 *
 * A donation site is a natural target for clickjacking — an invisible frame
 * over a "Donate" button sends money somewhere else — so framing is denied
 * outright. The referrer policy keeps donation references and applicant status
 * tokens out of the Referer header when someone follows a link off-site.
 */
const SECURITY_HEADERS = [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Content-Security-Policy", value: "frame-ancestors 'none'" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  // payment stays self-enabled: checkout redirects off-site today, but an
  // embedded Apple Pay or Google Pay button would need it and would fail
  // silently without it.
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=(self)" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  serverExternalPackages: ["@electric-sql/pglite", "pg"],
  async headers() {
    return [{ source: "/:path*", headers: SECURITY_HEADERS }];
  },
};

export default nextConfig;
