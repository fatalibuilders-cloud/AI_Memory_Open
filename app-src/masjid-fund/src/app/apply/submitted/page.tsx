import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Application received",
  robots: { index: false, follow: false },
};

export default async function ApplicationSubmittedPage({
  searchParams,
}: {
  searchParams: Promise<{ ref?: string; token?: string }>;
}) {
  const { ref, token } = await searchParams;

  return (
    <div className="mx-auto max-w-2xl px-4 py-20">
      <div className="rounded-3xl border border-sand-200 bg-white p-8 shadow-sm sm:p-10">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brass-600">
          Jazakum Allahu khayran
        </p>
        <h1 className="mt-3 font-display text-3xl font-semibold sm:text-4xl">
          Your application is with us
        </h1>
        <p className="mt-4 leading-relaxed text-sand-700">
          We check the title deed and trust registration, review the bill of quantities, and
          arrange a site visit before any project is listed. That usually takes a few weeks — and
          if something is missing, we will ask you for it rather than turning the application
          down.
        </p>

        {ref && (
          <dl className="mt-8 divide-y divide-sand-200 rounded-2xl border border-sand-200">
            <div className="flex flex-wrap items-center justify-between gap-2 px-5 py-3">
              <dt className="text-sm text-sand-700">Reference</dt>
              <dd className="font-semibold">{ref}</dd>
            </div>
          </dl>
        )}

        {token && (
          <div className="mt-6 rounded-2xl bg-masjid-50 p-5">
            <p className="font-semibold text-masjid-800">Keep this link</p>
            <p className="mt-1 text-sm leading-relaxed text-masjid-800/85">
              It shows the progress of your application and anything we still need. We have also
              emailed it to you.
            </p>
            <Link
              href={`/apply/status/${token}`}
              className="mt-3 inline-block break-all rounded-lg bg-white px-3 py-2 text-sm font-medium text-masjid-700 underline"
            >
              /apply/status/{token.slice(0, 12)}…
            </Link>
          </div>
        )}

        <div className="mt-8 flex flex-wrap gap-3">
          {token && (
            <Link
              href={`/apply/status/${token}`}
              className="rounded-xl bg-masjid-700 px-6 py-3.5 font-semibold text-white hover:bg-masjid-800"
            >
              Track your application
            </Link>
          )}
          <Link
            href="/projects"
            className="rounded-xl border border-masjid-700 px-6 py-3.5 font-semibold text-masjid-700 hover:bg-masjid-50"
          >
            See masajid being built
          </Link>
        </div>
      </div>
    </div>
  );
}
