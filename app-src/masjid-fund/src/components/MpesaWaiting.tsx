"use client";

import { useEffect, useState } from "react";

/**
 * The M-Pesa rail has no page to redirect to — the prompt arrives on the
 * donor's phone. This watches the donation until Safaricom's callback settles
 * it, so the donor sees the outcome without refreshing.
 */
export function MpesaWaiting({
  reference,
  phoneHint,
  simulated,
}: {
  reference: string;
  /** Last three digits, so the donor can tell which phone to look at. */
  phoneHint: string | null;
  /** True when no Daraja credentials are configured and this is a rehearsal. */
  simulated: boolean;
}) {
  const [status, setStatus] = useState<"pending" | "completed" | "failed">("pending");
  const [waitedSeconds, setWaited] = useState(0);

  useEffect(() => {
    if (status !== "pending") return;

    const started = Date.now();
    const timer = setInterval(async () => {
      setWaited(Math.round((Date.now() - started) / 1000));
      try {
        const res = await fetch(`/api/donations/${encodeURIComponent(reference)}`, {
          cache: "no-store",
        });
        if (!res.ok) return;
        const data = (await res.json()) as { status: "pending" | "completed" | "failed" };
        if (data.status === "completed") {
          window.location.href = `/donate/thank-you?ref=${encodeURIComponent(reference)}`;
        } else if (data.status === "failed") {
          setStatus("failed");
        }
      } catch {
        // A dropped poll is not worth showing; the next one will do.
      }
    }, 3000);

    return () => clearInterval(timer);
  }, [reference, status]);

  if (status === "failed") {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
        <p className="font-display text-xl font-semibold text-red-800">
          That payment did not go through
        </p>
        <p className="mt-2 leading-relaxed text-red-800/90">
          The prompt may have been cancelled or timed out. Nothing has been charged.
        </p>
        <a
          href="/donate"
          className="mt-5 inline-block rounded-xl bg-masjid-700 px-6 py-3.5 font-semibold text-white hover:bg-masjid-800"
        >
          Try again
        </a>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-sand-200 bg-white p-6 text-center">
      <div
        className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-sand-200 border-t-masjid-700"
        role="status"
        aria-label="Waiting for your M-Pesa PIN"
      />
      <p className="mt-5 font-display text-xl font-semibold">Check your phone</p>
      <p className="mt-2 leading-relaxed text-sand-700">
        {simulated
          ? "In a live deployment an M-Pesa prompt would arrive on your phone now. This is a rehearsal — use the buttons below to play out either ending."
          : `Enter your M-Pesa PIN on the prompt we have just sent${
              phoneHint ? ` to the number ending ${phoneHint}` : ""
            }. This page updates by itself.`}
      </p>
      {waitedSeconds > 45 && !simulated && (
        <p className="mt-4 rounded-xl bg-sand-100 px-4 py-3 text-sm text-sand-800">
          Still waiting. If no prompt arrived, check the number and try again — nothing has been
          charged.
        </p>
      )}
    </div>
  );
}
