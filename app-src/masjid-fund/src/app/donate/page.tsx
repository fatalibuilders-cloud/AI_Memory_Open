import type { Metadata } from "next";
import { DonateForm } from "@/components/DonateForm";
import { MAX_DONATION_CENTS, MIN_DONATION_CENTS } from "@/lib/money";
import { getPaymentProvider } from "@/lib/payments";
import { listProjects } from "@/lib/projects";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Donate",
  description:
    "Give once or monthly towards the construction of a masjid. Choose a project, choose an amount, and receive a receipt by email.",
};

export default async function DonatePage({
  searchParams,
}: {
  searchParams: Promise<{ project?: string; frequency?: string; amount?: string; cancelled?: string }>;
}) {
  const params = await searchParams;
  const projects = (await listProjects()).filter((p) => p.status !== "completed");
  const liveMode = getPaymentProvider().liveMode;

  const requested = Number(params.amount);
  const defaultAmountCents =
    Number.isFinite(requested) && requested >= MIN_DONATION_CENTS && requested <= MAX_DONATION_CENTS
      ? Math.round(requested)
      : undefined;

  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <header>
        <h1 className="font-display text-4xl font-semibold sm:text-5xl">Give to build a masjid</h1>
        <p className="mt-4 text-lg leading-relaxed text-sand-700">
          Your gift goes to construction — blocks, roofing, water and finishes — on a project
          with land already secured and a local committee in place.
        </p>
      </header>

      {params.cancelled && (
        <p className="mt-8 rounded-xl border border-brass-400 bg-brass-400/10 px-4 py-3 text-sm text-sand-800">
          Your donation was not completed, so nothing has been charged. You can start again
          below whenever you are ready.
        </p>
      )}

      <div className="mt-10">
        <DonateForm
          projects={projects.map((p) => ({
            slug: p.slug,
            name: p.name,
            city: p.city,
            country: p.country,
          }))}
          defaultProjectSlug={params.project ?? ""}
          defaultFrequency={params.frequency === "monthly" ? "monthly" : "one_time"}
          defaultAmountCents={defaultAmountCents}
          liveMode={liveMode}
        />
      </div>
    </div>
  );
}
