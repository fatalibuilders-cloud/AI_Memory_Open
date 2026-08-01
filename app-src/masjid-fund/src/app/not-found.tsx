import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[50vh] max-w-md flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="font-display text-2xl font-semibold">Page not found</h1>
      <p className="text-sand-700">That page doesn&apos;t exist — the projects are this way.</p>
      <Link
        href="/projects"
        className="rounded-xl bg-masjid-700 px-5 py-3 font-semibold text-white hover:bg-masjid-800"
      >
        Browse projects
      </Link>
    </div>
  );
}
