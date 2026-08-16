import Link from "next/link";
import { redirect } from "next/navigation";
import { getAdminSession } from "@/lib/admin";
import { ApplicationStatusPill } from "@/components/admin/ApplicationStatusPill";
import { APPLICATION_STATUSES, STATUS_LABELS, listApplications } from "@/lib/applications";
import { formatMoney } from "@/lib/money";

export const dynamic = "force-dynamic";

export default async function AdminApplicationsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  if (!(await getAdminSession())) redirect("/admin/login");

  const { status } = await searchParams;
  const filter = (APPLICATION_STATUSES as readonly string[]).includes(status ?? "")
    ? status
    : undefined;
  const applications = await listApplications(filter);

  return (
    <div>
      <h1 className="font-display text-3xl font-semibold">Applications</h1>
      <p className="mt-2 text-sand-700">
        Communities asking to have a masjid funded. Nothing here is public until it is published
        as a project.
      </p>

      <nav className="mt-6 flex flex-wrap gap-2 text-sm">
        <Link
          href="/admin/applications"
          className={`rounded-lg px-3 py-1.5 font-medium ${
            !filter ? "bg-masjid-700 text-white" : "border border-sand-200 bg-white"
          }`}
        >
          all
        </Link>
        {APPLICATION_STATUSES.map((value) => (
          <Link
            key={value}
            href={`/admin/applications?status=${value}`}
            className={`rounded-lg px-3 py-1.5 font-medium ${
              filter === value ? "bg-masjid-700 text-white" : "border border-sand-200 bg-white"
            }`}
          >
            {STATUS_LABELS[value].toLowerCase()}
          </Link>
        ))}
      </nav>

      <div className="mt-4 overflow-x-auto rounded-2xl border border-sand-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-sand-200 text-left text-sand-700">
            <tr>
              <th className="p-3 font-medium">Reference</th>
              <th className="p-3 font-medium">Masjid</th>
              <th className="p-3 font-medium">Cost</th>
              <th className="p-3 font-medium">Contact</th>
              <th className="p-3 font-medium">Status</th>
              <th className="p-3 font-medium">Received</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-sand-200">
            {applications.map((application) => (
              <tr key={application.id}>
                <td className="p-3 font-mono text-xs">
                  <Link
                    href={`/admin/applications/${application.id}`}
                    className="font-semibold text-masjid-700 hover:underline"
                  >
                    {application.reference}
                  </Link>
                </td>
                <td className="p-3">
                  <span className="font-semibold">{application.masjidName}</span>
                  <span className="block text-xs text-sand-700">
                    {application.city}, {application.country}
                  </span>
                </td>
                <td className="p-3">
                  {formatMoney(application.estimatedCostCents, application.currency)}
                </td>
                <td className="p-3">
                  {application.contactName}
                  <span className="block text-xs text-sand-700">{application.contactPhone}</span>
                </td>
                <td className="p-3">
                  <ApplicationStatusPill status={application.status} />
                </td>
                <td className="p-3 text-xs text-sand-700">
                  {new Date(application.createdAt).toLocaleDateString("en-GB")}
                </td>
              </tr>
            ))}
            {applications.length === 0 && (
              <tr>
                <td colSpan={6} className="p-6 text-center text-sand-700">
                  No applications with this status.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
