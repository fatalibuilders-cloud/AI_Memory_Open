import Link from "next/link";

export function ExportBar({ projectId, hasAccess }: { projectId: string; hasAccess: boolean }) {
  if (!hasAccess) {
    return (
      <div className="flex flex-col items-start gap-2 rounded-xl border border-amber-300 bg-amber-50 p-4">
        <p className="text-sm font-medium text-amber-900">
          Download this estimate as Excel and share it on WhatsApp
        </p>
        <Link
          href="/pricing"
          className="rounded-lg bg-amber-700 px-4 py-2 text-sm font-medium text-white hover:bg-amber-800"
        >
          Unlock with lifetime access — $30
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <a
        href={`/api/projects/${projectId}/export`}
        className="rounded-lg bg-green-700 px-4 py-2 text-sm font-medium text-white hover:bg-green-800"
      >
        ⬇ Download Excel (BOQ)
      </a>
    </div>
  );
}
