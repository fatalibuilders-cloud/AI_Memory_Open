import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { getUserBySession } from "@/lib/auth";
import { readSessionCookie } from "@/lib/session-cookie";

export const metadata: Metadata = { title: "Account — Fatalibuilders" };
export const dynamic = "force-dynamic";

export default async function AccountPage() {
  const user = await getUserBySession(await readSessionCookie());
  if (!user) redirect("/login");

  return (
    <main className="mx-auto flex max-w-md flex-col gap-6 px-6 py-16">
      <h1 className="text-3xl font-bold">Your account</h1>
      <div className="rounded-2xl border border-stone-200 bg-white p-6">
        <dl className="space-y-3 text-sm">
          <div>
            <dt className="font-medium text-stone-500">Email</dt>
            <dd className="text-base">{user.email}</dd>
          </div>
          <div>
            <dt className="font-medium text-stone-500">Access</dt>
            <dd className="text-base">
              {user.lifetimeAccess ? (
                <span className="font-medium text-green-700">✓ Lifetime access</span>
              ) : (
                <span>
                  Free preview —{" "}
                  <Link href="/pricing" className="font-medium text-amber-700 hover:underline">
                    get lifetime access for $30
                  </Link>
                </span>
              )}
            </dd>
          </div>
        </dl>
      </div>
      <form action="/api/auth/logout" method="post">
        <button
          type="submit"
          className="rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100"
        >
          Sign out
        </button>
      </form>
    </main>
  );
}
