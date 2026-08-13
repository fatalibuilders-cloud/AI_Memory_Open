import Link from "next/link";
import { redirect } from "next/navigation";
import { getAdminSession } from "@/lib/admin";
import { getAdminStats, listDonationsForAdmin } from "@/lib/admin-data";
import { formatMoney } from "@/lib/money";
import { getEmailProvider } from "@/lib/email";
import { getPaymentProvider } from "@/lib/payments";
import { getOrg } from "@/lib/org";

export const dynamic = "force-dynamic";

export default async function AdminDashboard() {
  if (!(await getAdminSession())) redirect("/admin/login");

  const [stats, recent] = await Promise.all([getAdminStats(), listDonationsForAdmin({ limit: 10 })]);
  const payments = getPaymentProvider();
  const email = getEmailProvider();
  const org = getOrg();

  const warnings = [
    !payments.liveMode && "Payments are simulated — set STRIPE_SECRET_KEY to take real money.",
    !email.live && "Email is log-only — set RESEND_API_KEY so donors receive receipts.",
    !org.registered && "No registration number configured — receipts carry no charity status.",
    stats.failedEmailCount > 0 &&
      `${stats.failedEmailCount} email${stats.failedEmailCount === 1 ? "" : "s"} failed to send.`,
  ].filter(Boolean) as string[];

  return (
    <div>
      <h1 className="font-display text-3xl font-semibold">Dashboard</h1>

      {warnings.length > 0 && (
        <ul className="mt-6 space-y-2">
          {warnings.map((warning) => (
            <li
              key={warning}
              className="rounded-xl border border-brass-400 bg-brass-400/10 px-4 py-3 text-sm text-sand-800"
            >
              {warning}
            </li>
          ))}
        </ul>
      )}

      <dl className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Tile label="Settled donations" value={formatMoney(stats.settledCents)} />
        <Tile label="Last 30 days" value={formatMoney(stats.last30DaysCents)} />
        <Tile label="Active monthly gifts" value={String(stats.monthlyActiveCount)} />
        <Tile
          label="Pending / failed"
          value={`${stats.pendingCount} / ${stats.failedCount}`}
          muted
        />
      </dl>

      <section className="mt-12">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-2xl font-semibold">Latest donations</h2>
          <Link href="/admin/donations" className="font-semibold text-masjid-700 hover:underline">
            All donations →
          </Link>
        </div>

        <div className="mt-4 overflow-x-auto rounded-2xl border border-sand-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-sand-200 text-left text-sand-700">
              <tr>
                <th className="p-3 font-medium">Reference</th>
                <th className="p-3 font-medium">Amount</th>
                <th className="p-3 font-medium">Project</th>
                <th className="p-3 font-medium">Status</th>
                <th className="p-3 font-medium">Received</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-sand-200">
              {recent.map((donation) => (
                <tr key={donation.reference}>
                  <td className="p-3 font-mono text-xs">{donation.reference}</td>
                  <td className="p-3 font-semibold">
                    {formatMoney(donation.amountCents, donation.currency)}
                    {donation.frequency === "monthly" ? "/mo" : ""}
                  </td>
                  <td className="p-3">{donation.projectName ?? "Where needed most"}</td>
                  <td className="p-3">{donation.status}</td>
                  <td className="p-3 text-sand-700">
                    {new Date(donation.completedAt ?? donation.createdAt).toLocaleString("en-GB")}
                  </td>
                </tr>
              ))}
              {recent.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-6 text-center text-sand-700">
                    No donations yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Tile({ label, value, muted }: { label: string; value: string; muted?: boolean }) {
  return (
    <div className="rounded-2xl border border-sand-200 bg-white p-5">
      <dt className="text-xs uppercase tracking-wide text-sand-700">{label}</dt>
      <dd
        className={`mt-1 font-display text-2xl font-semibold ${
          muted ? "text-sand-800" : "text-masjid-700"
        }`}
      >
        {value}
      </dd>
    </div>
  );
}
