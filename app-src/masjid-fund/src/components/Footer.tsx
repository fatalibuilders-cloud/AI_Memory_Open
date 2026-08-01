import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-20 border-t border-sand-200 bg-masjid-900 text-sand-100">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div className="sm:col-span-2">
          <p className="font-display text-xl font-semibold text-white">Masjid Fund</p>
          <p className="mt-3 max-w-sm text-sm leading-relaxed text-sand-200/80">
            Every masjid we build is titled to a local waqf trust, so it stays a place of
            prayer for good and can never be sold.
          </p>
        </div>

        <nav className="text-sm">
          <p className="font-semibold text-white">Give</p>
          <ul className="mt-3 space-y-2 text-sand-200/80">
            <li>
              <Link href="/projects" className="hover:text-white">
                Building projects
              </Link>
            </li>
            <li>
              <Link href="/donate" className="hover:text-white">
                Donate
              </Link>
            </li>
            <li>
              <Link href="/donate?frequency=monthly" className="hover:text-white">
                Give monthly
              </Link>
            </li>
          </ul>
        </nav>

        <nav className="text-sm">
          <p className="font-semibold text-white">About</p>
          <ul className="mt-3 space-y-2 text-sand-200/80">
            <li>
              <Link href="/about" className="hover:text-white">
                How it works
              </Link>
            </li>
            <li>
              <Link href="/faq" className="hover:text-white">
                Questions
              </Link>
            </li>
            <li>
              <a href="mailto:salam@masjidfund.example" className="hover:text-white">
                Contact us
              </a>
            </li>
          </ul>
        </nav>
      </div>

      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-xs text-sand-200/70 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} Masjid Fund. All rights reserved.</p>
          <p>
            Project figures are published from the build accounts. Donation receipts are
            issued by email for every completed gift.
          </p>
        </div>
      </div>
    </footer>
  );
}
