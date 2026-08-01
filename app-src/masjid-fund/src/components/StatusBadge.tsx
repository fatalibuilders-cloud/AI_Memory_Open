import type { ProjectStatus } from "@/lib/projects";

const STYLES: Record<ProjectStatus, { label: string; className: string }> = {
  planning: { label: "Preparing to build", className: "bg-brass-400/20 text-brass-600" },
  building: { label: "Under construction", className: "bg-masjid-100 text-masjid-700" },
  completed: { label: "Completed", className: "bg-masjid-800 text-sand-100" },
};

export function StatusBadge({ status }: { status: ProjectStatus }) {
  const style = STYLES[status] ?? STYLES.planning;
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${style.className}`}
    >
      {style.label}
    </span>
  );
}
