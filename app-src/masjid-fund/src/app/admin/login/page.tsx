import { redirect } from "next/navigation";
import { getAdminSession, loginMode } from "@/lib/admin";
import { loginAction } from "../actions";

export const dynamic = "force-dynamic";

export default async function AdminLoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  if (await getAdminSession()) redirect("/admin");
  const { error } = await searchParams;
  const mode = loginMode();

  return (
    <div className="mx-auto max-w-md py-10">
      <h1 className="font-display text-3xl font-semibold">Staff sign in</h1>

      {mode === "dev" && (
        <p className="mt-4 rounded-xl border border-brass-400 bg-brass-400/10 px-4 py-3 text-sm text-sand-800">
          No admin credentials are configured, so development sign-in is active:{" "}
          <strong>admin@localhost</strong> / <strong>masjidfund-dev</strong>. Set{" "}
          <code>ADMIN_EMAIL</code> and <code>ADMIN_PASSWORD_HASH</code> before deploying — this
          fallback is disabled in production.
        </p>
      )}
      {mode === "disabled" && (
        <p className="mt-4 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          Admin access is not configured on this deployment. Set <code>ADMIN_EMAIL</code> and{" "}
          <code>ADMIN_PASSWORD_HASH</code> (generate one with{" "}
          <code>npm run admin:hash -- &apos;password&apos;</code>).
        </p>
      )}

      <form action={loginAction} className="mt-8 space-y-4">
        <label className="block">
          <span className="text-sm font-medium">Email</span>
          <input
            name="email"
            type="email"
            required
            autoComplete="username"
            className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
          />
        </label>
        <label className="block">
          <span className="text-sm font-medium">Password</span>
          <input
            name="password"
            type="password"
            required
            autoComplete="current-password"
            className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
          />
        </label>

        {error && (
          <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <button
          type="submit"
          className="w-full rounded-xl bg-masjid-700 px-6 py-3.5 font-semibold text-white hover:bg-masjid-800"
        >
          Sign in
        </button>
      </form>
    </div>
  );
}
