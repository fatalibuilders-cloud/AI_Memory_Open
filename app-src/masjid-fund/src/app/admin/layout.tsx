import type { Metadata } from "next";
import Link from "next/link";
import { getAdminSession } from "@/lib/admin";
import { logoutAction } from "./actions";

export const metadata: Metadata = {
  title: "Admin",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

const NAV = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/projects", label: "Projects" },
  { href: "/admin/donations", label: "Donations" },
];

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const session = await getAdminSession();

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      {session && (
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-sand-200 pb-4">
          <nav className="flex flex-wrap gap-1 text-sm">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-lg px-3 py-2 font-medium text-masjid-800 hover:bg-sand-100"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <form action={logoutAction} className="flex items-center gap-3 text-sm">
            <span className="text-sand-700">{session.email}</span>
            <button type="submit" className="font-semibold text-masjid-700 hover:underline">
              Sign out
            </button>
          </form>
        </div>
      )}
      {children}
    </div>
  );
}
