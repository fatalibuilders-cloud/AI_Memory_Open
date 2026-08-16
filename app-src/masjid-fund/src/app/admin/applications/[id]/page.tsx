import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { ApplicationStatusPill } from "@/components/admin/ApplicationStatusPill";
import { ProjectFields } from "@/components/admin/ProjectFields";
import { getAdminSession } from "@/lib/admin";
import {
  LAND_OWNERSHIP_LABELS,
  STATUS_LABELS,
  getApplicationById,
  listApplicationEvents,
} from "@/lib/applications";
import { FILE_KINDS } from "@/lib/files";
import { formatMoney } from "@/lib/money";
import { publishApplicationAction, setApplicationStatusAction } from "../../actions";

export const dynamic = "force-dynamic";

export default async function AdminApplicationPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ error?: string; saved?: string }>;
}) {
  if (!(await getAdminSession())) redirect("/admin/login");

  const { id } = await params;
  const { error, saved } = await searchParams;
  const application = await getApplicationById(id);
  if (!application) notFound();

  const events = await listApplicationEvents(id);
  const setStatus = setApplicationStatusAction.bind(null, id);
  const publish = publishApplicationAction.bind(null, id);

  // A sensible starting point for the project; staff can change any of it.
  const suggestedSlug = `${application.masjidName}-${application.city}`
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 60);

  return (
    <div className="max-w-3xl">
      <Link href="/admin/applications" className="text-sm text-sand-700 hover:text-masjid-900">
        ← Applications
      </Link>

      <div className="mt-3 flex flex-wrap items-center gap-3">
        <h1 className="font-display text-3xl font-semibold">{application.masjidName}</h1>
        <ApplicationStatusPill status={application.status} />
      </div>
      <p className="mt-2 text-sand-700">
        {application.reference} · {application.city}, {application.country} · received{" "}
        {new Date(application.createdAt).toLocaleDateString("en-GB")}
      </p>

      {saved && (
        <p className="mt-6 rounded-xl bg-masjid-50 px-4 py-3 text-sm text-masjid-800">Saved.</p>
      )}
      {error && (
        <p role="alert" className="mt-6 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {/* Documents first — they are what the review turns on. */}
      <section className="mt-10">
        <h2 className="font-display text-2xl font-semibold">Documents</h2>
        <ul className="mt-4 divide-y divide-sand-200 overflow-hidden rounded-2xl border border-sand-200 bg-white">
          {application.documents.map((doc) => (
            <li key={doc.id} className="flex flex-wrap items-center justify-between gap-3 p-4">
              <div>
                <p className="font-semibold">
                  {FILE_KINDS.find((k) => k.kind === doc.kind)?.label ?? doc.kind}
                </p>
                <p className="text-xs text-sand-700">
                  {doc.filename} · {(doc.byteSize / 1024).toFixed(0)} KB · {doc.contentType}
                </p>
              </div>
              <a
                href={`/admin/applications/documents/${doc.id}`}
                className="rounded-lg border border-masjid-700 px-3.5 py-1.5 text-sm font-semibold text-masjid-700 hover:bg-masjid-50"
              >
                Download
              </a>
            </li>
          ))}
          {application.documents.length === 0 && (
            <li className="p-4 text-sand-700">No documents attached.</li>
          )}
        </ul>
        <p className="mt-2 text-xs text-sand-700">
          Files download rather than open in the browser, and are never reachable without a staff
          session.
        </p>
      </section>

      <section className="mt-10">
        <h2 className="font-display text-2xl font-semibold">What they told us</h2>
        <dl className="mt-4 grid gap-3 sm:grid-cols-2">
          <Fact label="Capacity when built" value={`${application.capacityPlanned} worshippers`} />
          <Fact label="Praying there now" value={String(application.congregationNow)} />
          <Fact
            label="Estimated cost"
            value={formatMoney(application.estimatedCostCents, application.currency)}
          />
          <Fact
            label="Raised locally"
            value={formatMoney(application.alreadyRaisedCents, application.currency)}
          />
          <Fact label="Title deed number" value={application.landTitleNumber} />
          <Fact label="Title held by" value={LAND_OWNERSHIP_LABELS[application.landOwnership]} />
          <Fact
            label="Held by a trust?"
            value={application.titledToTrust ? "Yes, they say" : "No — check this carefully"}
          />
          <Fact
            label="Trust"
            value={
              application.trustName
                ? `${application.trustName}${
                    application.trustRegistration ? ` (${application.trustRegistration})` : ""
                  }`
                : "Not given"
            }
          />
          <Fact
            label="Contact"
            value={`${application.contactName} — ${application.contactRole}`}
          />
          <Fact label="Reach them on" value={`${application.contactEmail} · ${application.contactPhone}`} />
          {application.locationNote && <Fact label="Where exactly" value={application.locationNote} />}
        </dl>

        <div className="mt-4 rounded-2xl border border-sand-200 bg-white p-5">
          <p className="text-xs uppercase tracking-wide text-sand-700">In their words</p>
          <p className="mt-2 whitespace-pre-line leading-relaxed">{application.story}</p>
        </div>
      </section>

      {/* Decision */}
      <section className="mt-12">
        <h2 className="font-display text-2xl font-semibold">Move it along</h2>
        <p className="mt-1 text-sand-700">
          The note is emailed to the applicant and shown on their status page, so write it for
          them.
        </p>

        <form action={setStatus} className="mt-4 space-y-3 rounded-2xl border border-sand-200 bg-white p-5">
          <label className="block">
            <span className="text-sm font-medium">Note to the applicant</span>
            <textarea
              name="note"
              rows={3}
              defaultValue=""
              placeholder="We have the deed and the drawings — we still need the priced bill of quantities before the site visit."
              className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <button
              type="submit"
              name="status"
              value="in_review"
              className="rounded-xl border border-sand-300 px-4 py-2.5 font-semibold hover:bg-sand-100"
            >
              Mark under review
            </button>
            <button
              type="submit"
              name="status"
              value="needs_info"
              className="rounded-xl border border-brass-500 px-4 py-2.5 font-semibold text-brass-600 hover:bg-brass-400/10"
            >
              Ask for more
            </button>
            <button
              type="submit"
              name="status"
              value="rejected"
              className="rounded-xl border border-red-300 px-4 py-2.5 font-semibold text-red-700 hover:bg-red-50"
            >
              Decline
            </button>
          </div>
          <p className="text-xs text-sand-700">
            A note is required when asking for more or declining. Approval happens by publishing
            the project below.
          </p>
        </form>
      </section>

      {/* Publish */}
      <section className="mt-12">
        <h2 className="font-display text-2xl font-semibold">Publish as a project</h2>

        {application.projectSlug ? (
          <p className="mt-3 rounded-2xl bg-masjid-50 p-5 leading-relaxed text-masjid-800">
            Published as{" "}
            <Link href={`/admin/projects/${application.projectSlug}`} className="font-semibold underline">
              {application.projectSlug}
            </Link>
            . Edit the project there — the applicant has been told it is live.
          </p>
        ) : (
          <>
            <p className="mt-1 text-sand-700">
              Check every figure before publishing: this is what donors will see, and the budget
              becomes the fundraising goal. Costs quoted in{" "}
              {application.currency === "KES" ? "KES need converting to USD" : "USD carry over"}.
            </p>
            <form action={publish} className="mt-4 space-y-6">
              <ProjectFields
                project={{
                  id: "",
                  slug: suggestedSlug,
                  name: application.masjidName,
                  city: application.city,
                  country: application.country,
                  summary: "",
                  story: application.story,
                  status: "planning",
                  goalCents:
                    application.currency === "USD" ? application.estimatedCostCents : 0,
                  raisedCents: 0,
                  offlineRaisedCents:
                    application.currency === "USD" ? application.alreadyRaisedCents : 0,
                  donorCount: 0,
                  capacity: application.capacityPlanned,
                  zakatEligible: false,
                  accent: "emerald",
                  position: 0,
                }}
              />
              <label className="block">
                <span className="text-sm font-medium">Note to the applicant (optional)</span>
                <textarea
                  name="note"
                  rows={2}
                  placeholder="Approved after the site visit on 4 September. The page is live now."
                  className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
                />
              </label>
              <button
                type="submit"
                className="rounded-xl bg-masjid-700 px-6 py-3.5 font-semibold text-white hover:bg-masjid-800"
              >
                Approve and publish
              </button>
            </form>
          </>
        )}
      </section>

      <section className="mt-12">
        <h2 className="font-display text-2xl font-semibold">History</h2>
        <ol className="mt-4 space-y-2 text-sm">
          {events.map((event) => (
            <li key={event.id} className="rounded-xl border border-sand-200 bg-white p-3">
              <span className="text-sand-700">
                {new Date(event.createdAt).toLocaleString("en-GB")} · {event.actor}
              </span>
              <span className="ml-2 font-semibold">
                {STATUS_LABELS[event.action as keyof typeof STATUS_LABELS] ?? event.action}
              </span>
              {event.note && <p className="mt-1 text-sand-700">{event.note}</p>}
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
