import Link from "next/link";

export function ExportBar({
  projectId,
  hasAccess,
  shareText,
}: {
  projectId: string;
  hasAccess: boolean;
  shareText: string;
}) {
  const waHref = `https://wa.me/?text=${encodeURIComponent(shareText)}`;

  return (
    <div className="flex flex-col gap-3">
      {hasAccess ? (
        <div className="flex flex-wrap items-center gap-3">
          <a
            href={`/api/projects/${projectId}/export`}
            className="rounded-lg bg-green-700 px-4 py-2 text-sm font-medium text-white hover:bg-green-800"
          >
            ⬇ Excel (BOQ)
          </a>
          <a
            href={`/api/projects/${projectId}/export-pdf`}
            className="rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800"
          >
            ⬇ PDF
          </a>
          <a
            href={waHref}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg bg-[#25D366] px-4 py-2 text-sm font-medium text-white hover:brightness-95"
          >
            Share on WhatsApp
          </a>
        </div>
      ) : (
        <div className="flex flex-col items-start gap-3 rounded-xl border border-amber-300 bg-amber-50 p-4">
          <p className="text-sm font-medium text-amber-900">
            Download this estimate as Excel or PDF and share it with clients
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/pricing"
              className="rounded-lg bg-amber-700 px-4 py-2 text-sm font-medium text-white hover:bg-amber-800"
            >
              Unlock exports — $30 lifetime
            </Link>
            <a
              href={waHref}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg bg-[#25D366] px-4 py-2 text-sm font-medium text-white hover:brightness-95"
            >
              Share on WhatsApp
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
