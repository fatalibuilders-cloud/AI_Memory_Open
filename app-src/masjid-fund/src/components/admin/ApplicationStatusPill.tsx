import { STATUS_LABELS, type ApplicationStatus } from "@/lib/application";

const STYLES: Record<ApplicationStatus, string> = {
  submitted: "bg-brass-400/20 text-brass-600",
  in_review: "bg-sand-200 text-sand-800",
  needs_info: "bg-red-50 text-red-700",
  approved: "bg-masjid-100 text-masjid-700",
  rejected: "bg-sand-100 text-sand-700",
};

export function ApplicationStatusPill({ status }: { status: ApplicationStatus }) {
  return (
    <span className={`inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${STYLES[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  );
}
