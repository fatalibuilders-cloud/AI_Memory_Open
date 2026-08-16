import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  APPLICATION_STATUSES,
  STATUS_LABELS,
  getApplicationByToken,
  listApplicationEvents,
} from "@/lib/applications";
import { FILE_KINDS } from "@/lib/files";
import { formatMoney } from "@/lib/money";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Your application",
  robots: { index: false, follow: false },
};

/** Progress an applicant sees; "rejected" is handled separately below. */
const STEPS = ["submitted", "in_review", "approved"] as const;

export default async function ApplicationStatusPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const application = await getApplicationByToken(token);
  if (!application) notFound();

  const events = await listApplicationEvents(application.id);
  const rejected = application.status === "rejected";
  const needsInfo = application.status === "needs_info";
  const reached = STEPS.indexOf(application.status as (typeof STEPS)[number]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brass-600">
        Application {application.reference}
      </p>
      <h1 className="mt-3 font-display text-4xl font-semibold">{application.masjidName}</h1>
      <p className="mt-2 text-sand-700">
        {application.city}, {application.country} · submitted{" "}
        {new Date(application.createdAt).toLocaleDateString("en-GB", {
          day: "numeric",
          month: "long",
          year: "numeric",
        })}
      </p>

      {/* Where it has got to */}
      <section className="mt-10 rounded-2xl border border-sand-200 bg-white p-6">
        {rejected ? (
          <>
            <h2 className="font-display text-xl font-semibold">Not accepted</h2>
            <p className="mt-2 leading-relaxed text-sand-700">
              We are not able to take this one forward. If circumstances change — a title
              transferred, a permit granted — you are welcome to apply again.
            </p>
          </>
        ) : (
          <ol className="space-y-4">
            {STEPS.map((step, i) => {
              const done = reached >= i;
              return (
                <li key={step} className="flex items-start gap-3">
                  <span
                    className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                      done ? "bg-masjid-700 text-white" : "bg-sand-200 text-sand-700"
                    }`}
                  >
                    {done ? "✓" : i + 1}
                  </span>
                  <div>
                    <p className={`font-semibold ${done ? "" : "text-sand-700"}`}>
                      {step === "submitted"
                        ? "Application received"
                        : step === "in_review"
                          ? "Documents and site being checked"
                          : "Approved and published for donations"}
                    </p>
                    {step === "in_review" && reached === 1 && (
                      <p className="mt-0.5 text-sm text-sand-700">
                        Title deed, trust registration, bill of quantities, then a site visit.
                      </p>
                    )}
                  </div>
                </li>
              );
            })}
          </ol>
        )}

        {needsInfo && (
          <div className="mt-6 rounded-xl border border-brass-400 bg-brass-400/10 p-4">
            <p className="font-semibold text-sand-800">We need something more</p>
            <p className="mt-1 leading-relaxed text-sand-800">
              {application.statusNote ?? "We have written to you with the details."}
            </p>
            <p className="mt-2 text-sm text-sand-700">
              Reply to our email with the missing documents and we will carry on from there.
            </p>
          </div>
        )}

        {application.statusNote && !needsInfo && (
          <p className="mt-6 rounded-xl bg-sand-100 p-4 leading-relaxed">
            {application.statusNote}
          </p>
        )}

        {application.projectSlug && (
          <Link
            href={`/projects/${application.projectSlug}`}
            className="mt-6 inline-block rounded-xl bg-masjid-700 px-6 py-3.5 font-semibold text-white hover:bg-masjid-800"
          >
            See your project page
          </Link>
        )}
      </section>

      {/* What we hold */}
      <section className="mt-10">
        <h2 className="font-display text-2xl font-semibold">What you sent us</h2>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2">
          <Fact label="Capacity when built" value={`${application.capacityPlanned} worshippers`} />
          <Fact
            label="Estimated cost"
            value={formatMoney(application.estimatedCostCents, application.currency)}
          />
          <Fact label="Title deed" value={application.landTitleNumber} />
          <Fact label="Contact" value={`${application.contactName} · ${application.contactRole}`} />
        </dl>

        <ul className="mt-4 flex flex-wrap gap-2">
          {application.documents.map((doc) => {
            const label = FILE_KINDS.find((k) => k.kind === doc.kind)?.label ?? doc.kind;
            return (
              <li
                key={doc.id}
                className="rounded-full border border-sand-200 bg-white px-3 py-1.5 text-sm"
              >
                {label} · {(doc.byteSize / 1024).toFixed(0)} KB
              </li>
            );
          })}
        </ul>
        <p className="mt-3 text-sm text-sand-700">
          Your documents and contact details are never published — only staff reviewing the
          application can open them.
        </p>
      </section>

      {/* History */}
      <section className="mt-10">
        <h2 className="font-display text-2xl font-semibold">History</h2>
        <ol className="mt-4 space-y-3 border-l-2 border-sand-200 pl-5">
          {events.map((event) => (
            <li key={event.id} className="relative">
              <span
                className="absolute -left-[27px] top-2 h-2.5 w-2.5 rounded-full bg-masjid-600"
                aria-hidden
              />
              <p className="text-sm text-sand-700">
                {new Date(event.createdAt).toLocaleString("en-GB")}
              </p>
              <p className="font-medium">
                {(APPLICATION_STATUSES as readonly string[]).includes(event.action)
                  ? STATUS_LABELS[event.action as keyof typeof STATUS_LABELS]
                  : event.action === "published"
                    ? "Published as a project"
                    : "Application submitted"}
              </p>
              {event.note && <p className="text-sm text-sand-700">{event.note}</p>}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-sand-200 bg-white p-4">
      <dt className="text-xs uppercase tracking-wide text-sand-700">{label}</dt>
      <dd className="mt-1 font-semibold">{value}</dd>
    </div>
  );
}
