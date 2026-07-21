import Link from "next/link";
import Image from "next/image";

export function Header() {
  return (
    <header className="sticky top-0 z-10 border-b border-stone-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <Image src="/icon.svg" alt="" width={28} height={28} priority />
          <span>Fatalibuilders</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/pricing" className="text-stone-600 hover:text-stone-900">
            Pricing
          </Link>
          <Link href="/account" className="text-stone-600 hover:text-stone-900">
            Account
          </Link>
          <Link
            href="/pricing"
            className="rounded-lg bg-amber-700 px-3 py-1.5 font-medium text-white hover:bg-amber-800"
          >
            Get lifetime access
          </Link>
        </nav>
      </div>
    </header>
  );
}
