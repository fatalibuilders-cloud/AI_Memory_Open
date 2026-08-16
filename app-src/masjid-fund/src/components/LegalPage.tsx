import { getOrg } from "@/lib/org";

/**
 * Shared shell for the policy pages, so they carry the same organisation
 * details and revision date without three copies of the same markup.
 */
export function LegalPage({
  title,
  intro,
  updated,
  children,
}: {
  title: string;
  intro: string;
  updated: string;
  children: React.ReactNode;
}) {
  const org = getOrg();

  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <h1 className="font-display text-4xl font-semibold sm:text-5xl">{title}</h1>
      <p className="mt-4 text-lg leading-relaxed text-sand-700">{intro}</p>
      <p className="mt-2 text-sm text-sand-700">Last updated {updated}.</p>

      <div className="mt-10 space-y-8 leading-relaxed [&_h2]:font-display [&_h2]:text-2xl [&_h2]:font-semibold [&_li]:mt-1 [&_p]:mt-3 [&_ul]:mt-3 [&_ul]:list-disc [&_ul]:pl-6">
        {children}
      </div>

      <footer className="mt-12 rounded-2xl border border-sand-200 bg-white p-6 text-sm">
        <p className="font-semibold">Who we are</p>
        <p className="mt-2 text-sand-700">
          {org.name}
          {org.registered ? (
            <>
              , registered with the {org.registrar} under {org.registration}
            </>
          ) : (
            <> (registration details not yet configured on this deployment)</>
          )}
          .
        </p>
        <p className="mt-1 text-sand-700">{org.address}</p>
        <p className="mt-1">
          <a href={`mailto:${org.email}`} className="text-masjid-700 underline">
            {org.email}
          </a>
        </p>
      </footer>
    </div>
  );
}
