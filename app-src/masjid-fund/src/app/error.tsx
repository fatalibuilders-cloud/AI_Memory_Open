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
    <div className="mx-auto flex min-h-[50vh] max-w-md flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="font-display text-2xl font-semibold">Something went wrong</h1>
      <p className="text-sand-700">
        Sorry — that didn&apos;t work. No donation has been charged. Try again, and if it keeps
        happening, email us and we will sort it out.
      </p>
      <button
        onClick={reset}
        className="rounded-xl bg-masjid-700 px-5 py-3 font-semibold text-white hover:bg-masjid-800"
      >
        Try again
      </button>
    </div>
  );
}
