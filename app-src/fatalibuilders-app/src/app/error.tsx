"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("App error boundary:", error);
  }, [error]);

  return (
    <main className="mx-auto flex min-h-[50vh] max-w-md flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-2xl font-bold">Something went wrong</h1>
      <p className="text-stone-600">
        Sorry — that didn&apos;t work. Your data is safe. Try again, and if it
        keeps happening, contact us.
      </p>
      <button
        onClick={reset}
        className="rounded-lg bg-amber-700 px-4 py-2 font-medium text-white hover:bg-amber-800"
      >
        Try again
      </button>
    </main>
  );
}
