export function Footer() {
  return (
    <footer className="border-t border-stone-200 bg-white">
      <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 py-6 text-sm text-stone-500 sm:flex-row sm:items-center sm:justify-between">
        <p>© {new Date().getFullYear()} Fatali Builders. All rights reserved.</p>
        <p className="text-xs">
          Results are estimates based on the selected design-code profile.
          Engineering outputs require review by a licensed engineer.
        </p>
      </div>
    </footer>
  );
}
