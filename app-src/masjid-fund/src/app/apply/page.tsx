import type { Metadata } from "next";
import { ApplyForm } from "@/components/ApplyForm";

export const metadata: Metadata = {
  title: "Apply for funding",
  description:
    "Apply to have your masjid built. Submit the certified title deed, drawings and bill of quantities, and we will review, verify and — if approved — publish it for donors to fund.",
};

const CHECKS = [
  {
    title: "Titled land",
    body: "A certified title deed, ideally held by a trust or society rather than an individual. If it is not yet, say so — transferring it is often part of the work.",
  },
  {
    title: "Drawings",
    body: "Floor plans and elevations for what you intend to build, whether or not the county has approved them yet.",
  },
  {
    title: "A priced bill of quantities",
    body: "Prepared by a quantity surveyor where possible. This is what we publish as the project budget, so donors can see what their money buys.",
  },
  {
    title: "A committee we can reach",
    body: "One named person who can answer questions and be there for the site visit.",
  },
];

export default function ApplyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <header>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brass-600">
          For communities
        </p>
        <h1 className="mt-3 font-display text-4xl font-semibold sm:text-5xl">
          Apply to have your masjid funded
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-sand-700">
          Tell us about the community, attach the paperwork, and we will verify it. Approved
          projects are published here with their full budget, and donors fund them stage by
          stage.
        </p>
      </header>

      <section className="mt-10 rounded-2xl border border-sand-200 bg-white p-6">
        <h2 className="font-display text-xl font-semibold">What you will need</h2>
        <dl className="mt-4 space-y-4">
          {CHECKS.map((check) => (
            <div key={check.title}>
              <dt className="font-semibold">{check.title}</dt>
              <dd className="mt-0.5 text-sm leading-relaxed text-sand-700">{check.body}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-5 border-t border-sand-200 pt-4 text-sm leading-relaxed text-sand-700">
          After you submit: we check the title deed and registration, review the bill of
          quantities, and arrange a site visit before anything is listed. That usually takes a few
          weeks. You will be able to track it, and we will come back to you if something is
          missing rather than simply refusing.
        </p>
      </section>

      <div className="mt-12">
        <ApplyForm />
      </div>
    </div>
  );
}
