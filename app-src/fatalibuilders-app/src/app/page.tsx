export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-6 px-6 text-center">
      <p className="text-sm font-semibold uppercase tracking-widest text-amber-700">
        Fatali Builders
      </p>
      <h1 className="text-4xl font-bold sm:text-5xl">
        Fatalibuilders Construction App
      </h1>
      <p className="max-w-xl text-lg text-stone-600">
        Enter your project once — get material quantities, cost estimates,
        labor plans, drawings and reports. Built on recognized design codes.
        One payment, lifetime access.
      </p>
      <p className="rounded-full border border-amber-300 bg-amber-100 px-4 py-1 text-sm font-medium text-amber-800">
        Under construction — Release 1.0 in progress
      </p>
    </main>
  );
}
