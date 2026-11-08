import type { Metadata } from "next";
import Link from "next/link";
import { AuthForm } from "@/components/AuthForm";

export const metadata: Metadata = { title: "Create account — Fatalibuilders" };

export default function SignupPage() {
  return (
    <main className="mx-auto flex max-w-md flex-col items-center gap-6 px-6 py-16 text-center">
      <div>
        <h1 className="text-3xl font-bold">Create your account</h1>
        <p className="mt-2 text-stone-600">
          Signing up is free. It unlocks the full workspace to try before you buy.
        </p>
      </div>

      {/* Lite vs. registered — honest framing for this app's $30-lifetime model.
          No account = a lite preview; a free account unlocks the full workspace
          to try; a one-time $30 at launch keeps every tool for life. */}
      <div className="w-full rounded-2xl border border-amber-200 bg-amber-50 p-5 text-left">
        <p className="font-semibold text-stone-800">What a free account unlocks</p>
        <ul className="mt-2 space-y-1.5 text-sm text-stone-700">
          <li>✓ Your own workspace — save projects instead of a one-off preview</li>
          <li>✓ Run full sample estimates: material quantities, costs and labor plans</li>
          <li>✓ Carry on where you left off from any device</li>
        </ul>
        <p className="mt-3 text-xs text-stone-500">
          Without an account you still get a lite preview of what the app does.
          Lifetime access to every tool is a one-time{" "}
          <span className="font-medium text-amber-800">$30</span> at launch — no subscription.
        </p>
      </div>

      <AuthForm mode="signup" />
      <p className="text-sm text-stone-500">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-amber-700 hover:underline">
          Sign in
        </Link>
      </p>
    </main>
  );
}
