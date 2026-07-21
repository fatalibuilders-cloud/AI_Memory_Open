import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing — Fatalibuilders Construction App",
  description: "One payment. Lifetime access. $30.",
};

export default function PricingPage() {
  return (
    <main className="mx-auto flex max-w-2xl flex-col items-center gap-6 px-6 py-16 text-center">
      <h1 className="text-3xl font-bold sm:text-4xl">One payment. Forever.</h1>
      <div className="w-full max-w-sm rounded-2xl border border-amber-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-widest text-amber-700">
          Lifetime access
        </p>
        <p className="mt-2 text-5xl font-bold">
          $30
          <span className="text-base font-normal text-stone-500"> once</span>
        </p>
        <ul className="mt-6 space-y-2 text-left text-sm text-stone-600">
          <li>✓ Material quantities</li>
          <li>✓ Itemized cost estimates</li>
          <li>✓ Labor &amp; time plans</li>
          <li>✓ Excel, PDF &amp; WhatsApp sharing</li>
          <li>✓ 2D drawings &amp; renders (coming)</li>
          <li>✓ Engineering reports (coming)</li>
        </ul>
        <button
          disabled
          className="mt-8 w-full cursor-not-allowed rounded-lg bg-stone-300 px-4 py-2.5 font-medium text-white"
          title="Checkout arrives with Release 1.0"
        >
          Checkout coming soon
        </button>
      </div>
      <p className="text-sm text-stone-500">
        Card payments worldwide and M-Pesa in Kenya — available at launch.
      </p>
    </main>
  );
}
