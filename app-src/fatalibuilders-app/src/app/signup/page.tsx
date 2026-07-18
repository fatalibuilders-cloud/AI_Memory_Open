import type { Metadata } from "next";
import Link from "next/link";
import { AuthForm } from "@/components/AuthForm";

export const metadata: Metadata = { title: "Create account — Fatalibuilders" };

export default function SignupPage() {
  return (
    <main className="mx-auto flex max-w-md flex-col items-center gap-6 px-6 py-16 text-center">
      <h1 className="text-3xl font-bold">Create your account</h1>
      <p className="text-stone-600">
        Free to sign up — run a sample calculation before you buy.
      </p>
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
