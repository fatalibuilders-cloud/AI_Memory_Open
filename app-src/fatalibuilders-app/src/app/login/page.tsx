import type { Metadata } from "next";
import Link from "next/link";
import { AuthForm } from "@/components/AuthForm";

export const metadata: Metadata = { title: "Sign in — Fatalibuilders" };

export default function LoginPage() {
  return (
    <main className="mx-auto flex max-w-md flex-col items-center gap-6 px-6 py-16 text-center">
      <h1 className="text-3xl font-bold">Welcome back</h1>
      <AuthForm mode="login" />
      <p className="text-sm text-stone-500">
        New here?{" "}
        <Link href="/signup" className="font-medium text-amber-700 hover:underline">
          Create an account
        </Link>
      </p>
    </main>
  );
}
