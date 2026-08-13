import Link from "next/link";
import { redirect } from "next/navigation";
import { getAdminSession } from "@/lib/admin";
import { listDonationsForAdmin } from "@/lib/admin-data";
import { INTENTS, INTENT_LABELS } from "@/lib/donation";
import { formatMoney } from "@/lib/money";
import { listProjects } from "@/lib/projects";
import { recordOfflineAction } from "../actions";

export const dynamic = "force-dynamic";

const STATUS_FILTERS = ["all", "completed", "pending", "failed"] as const;

export default async function AdminDonationsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string; error?: string; recorded?: string }>;
}) {
  if (!(await getAdminSession())) redirect("/admin/login");

  const { status, error, recorded } = await searchParams;
  const filter = status && status !== "all" ? status : undefined;
  const [donations, projects] = await Promise.all([
    listDonationsForAdmin({ status: filter, limit: 200 }),
    listProjects(),
  ]);

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="font-display text-3xl font-semibold">Donations</h1>
        <a
          href={`/admin/donations/export${filter ? `?status=${filter}` : ""}`}
          className="rounded-xl border border-masjid-700 px-5 py-3 font-semibold text-masjid-700 hover:bg-masjid-50"
        >
          Download CSV
        </a>
      </div>

      {recorded && (
        <p className="mt-6 rounded-xl bg-masjid-50 px-4 py-3 text-sm text-masjid-800">
          Offline gift recorded.
        </p>
      )}
      {error && (
        <p role="alert" className="mt-6 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <nav className="mt-6 flex flex-wrap gap-2 text-sm">
        {STATUS_FILTERS.map((value) => {
          const active = (status ?? "all") === value;
          return (
            <Link
              key={value}
              href={`/admin/donations${value === "all" ? "" : `?status=${value}`}`}
              className={`rounded-lg px-3 py-1.5 font-medium ${
                active ? "bg-masjid-700 text-white" : "border border-sand-200 bg-white"
              }`}
            >
              {value}
            </Link>
          );
        })}
      </nav>

      <div className="mt-4 overflow-x-auto rounded-2xl border border-sand-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-sand-200 text-left text-sand-700">
            <tr>
              <th className="p-3 font-medium">Reference</th>
              <th className="p-3 font-medium">Amount</th>
              <th className="p-3 font-medium">Donor</th>
              <th className="p-3 font-medium">Project</th>
              <th className="p-3 font-medium">Type</th>
              <th className="p-3 font-medium">Status</th>
              <th className="p-3 font-medium">Receipt</th>
              <th className="p-3 font-medium">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-sand-200">
            {donations.map((donation) => (
              <tr key={donation.reference}>
                <td className="p-3 font-mono text-xs">{donation.reference}</td>
                <td className="p-3 font-semibold">
                  {formatMoney(donation.amountCents, donation.currency)}
                  {donation.frequency === "monthly" ? "/mo" : ""}
                </td>
                <td className="p-3">
                  {donation.anonymous ? (
                    <span className="text-sand-700">Anonymous</span>
                  ) : (
                    donation.donorName ?? "—"
                  )}
                  <span className="block text-xs text-sand-700">{donation.donorEmail || "—"}</span>
                </td>
                <td className="p-3">{donation.projectName ?? "Where needed most"}</td>
                <td className="p-3 text-xs">
                  {INTENT_LABELS[donation.intent as keyof typeof INTENT_LABELS] ?? donation.intent}
                  <span className="block text-sand-700">{donation.provider}</span>
                </td>
                <td className="p-3">
                  {donation.status}
                  {donation.cancelledAt && (
                    <span className="block text-xs text-sand-700">cancelled</span>
                  )}
                </td>
                <td className="p-3 text-xs text-sand-700">
                  {donation.receiptSentAt ? "sent" : "—"}
                </td>
                <td className="p-3 text-xs text-sand-700">
                  {new Date(donation.completedAt ?? donation.createdAt).toLocaleString("en-GB")}
                </td>
              </tr>
            ))}
            {donations.length === 0 && (
              <tr>
                <td colSpan={8} className="p-6 text-center text-sand-700">
                  Nothing to show for this filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <section className="mt-14 max-w-2xl">
        <h2 className="font-display text-2xl font-semibold">Record an offline gift</h2>
        <p className="mt-1 text-sand-700">
          Bank transfer, M-Pesa paid direct, or cash handed to the committee. Recorded as
          settled, so it counts towards the project immediately. A receipt is emailed if you
          enter an address.
        </p>

        <form action={recordOfflineAction} className="mt-6 grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="text-sm font-medium">Amount received</span>
            <input
              name="amount"
              required
              placeholder="500"
              className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium">Project</span>
            <select
              name="projectSlug"
              className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
            >
              <option value="">Where it is needed most</option>
              {projects.map((project) => (
                <option key={project.slug} value={project.slug}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-sm font-medium">Donor name</span>
            <input
              name="donorName"
              className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium">Donor email (optional)</span>
            <input
              name="donorEmail"
              type="email"
              className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium">Type</span>
            <select
              name="intent"
              className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
            >
              {INTENTS.map((intent) => (
                <option key={intent} value={intent}>
                  {INTENT_LABELS[intent]}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-sm font-medium">Note (bank reference, receipt no.)</span>
            <input
              name="note"
              className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
            />
          </label>
          <label className="flex items-center gap-2 text-sm sm:col-span-2">
            <input type="checkbox" name="anonymous" className="h-4 w-4 rounded border-sand-300" />
            Record as anonymous
          </label>
          <div className="sm:col-span-2">
            <button
              type="submit"
              className="rounded-xl bg-masjid-700 px-6 py-3.5 font-semibold text-white hover:bg-masjid-800"
            >
              Record gift
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
