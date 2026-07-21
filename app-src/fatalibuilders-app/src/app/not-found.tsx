import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-[50vh] max-w-md flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-2xl font-bold">Page not found</h1>
      <p className="text-stone-600">That page doesn&apos;t exist.</p>
      <Link
        href="/"
        className="rounded-lg bg-amber-700 px-4 py-2 font-medium text-white hover:bg-amber-800"
      >
        Back to home
      </Link>
    </main>
  );
}
