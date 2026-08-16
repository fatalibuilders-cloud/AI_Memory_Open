"use client";

import { useState } from "react";
import {
  APPLICATION_CURRENCIES,
  LAND_OWNERSHIP,
  LAND_OWNERSHIP_LABELS,
} from "@/lib/application";
import { ACCEPTED_DESCRIPTION, FILE_KINDS } from "@/lib/files";

/**
 * Public application form. Submitted as multipart to /api/applications so the
 * documents travel with it; the server re-validates everything.
 */
export function ApplyForm() {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const res = await fetch("/api/applications", {
        method: "POST",
        body: new FormData(event.currentTarget),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.error ?? "We could not receive that application. Please try again.");
        setSubmitting(false);
        window.scrollTo({ top: 0, behavior: "smooth" });
        return;
      }
      window.location.href = `/apply/submitted?ref=${encodeURIComponent(
        data.reference,
      )}&token=${encodeURIComponent(data.statusToken)}`;
    } catch {
      setError("Network problem — check your connection and try again.");
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-10" noValidate>
      {error && (
        <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <Section title="1. The masjid" hint="What is being built, and for whom.">
        <Field label="Proposed name of the masjid" name="masjidName" required />
        <Field label="Town or city" name="city" required />
        <Field label="Country" name="country" required />
        <Field
          label="Where exactly"
          name="locationNote"
          hint="Ward, landmark or plot location — enough for a site visit."
        />
        <Field
          label="People praying there now"
          name="congregationNow"
          type="number"
          hint="Roughly, at jumu'ah."
        />
        <Field
          label="Capacity when built"
          name="capacityPlanned"
          type="number"
          required
          hint="Worshippers the new masjid will hold."
        />
      </Section>

      <Section
        title="2. The land"
        hint="We only fund construction on land that is titled and cannot be sold from under the community."
      >
        <Field label="Title deed number" name="landTitleNumber" required />
        <label className="block">
          <span className="text-sm font-medium">Who holds the title?</span>
          <select
            name="landOwnership"
            defaultValue="waqf_trust"
            className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
          >
            {LAND_OWNERSHIP.map((value) => (
              <option key={value} value={value}>
                {LAND_OWNERSHIP_LABELS[value]}
              </option>
            ))}
          </select>
        </label>
        <Field label="Name of the trust or society" name="trustName" />
        <Field label="Trust registration number" name="trustRegistration" />
        <label className="flex items-start gap-3 text-sm sm:col-span-2">
          <input
            type="checkbox"
            name="titledToTrust"
            className="mt-0.5 h-4 w-4 rounded border-sand-300 text-masjid-700"
          />
          <span>
            The title is held by a trust or society, not by an individual. If it is not, apply
            anyway and tell us the situation in the description — transferring the title is often
            part of the work.
          </span>
        </label>
      </Section>

      <Section title="3. What it costs" hint="From your bill of quantities.">
        <label className="block">
          <span className="text-sm font-medium">Currency</span>
          <select
            name="currency"
            defaultValue="USD"
            className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
          >
            {APPLICATION_CURRENCIES.map((currency) => (
              <option key={currency} value={currency}>
                {currency}
              </option>
            ))}
          </select>
        </label>
        <Field
          label="Estimated total cost"
          name="estimatedCost"
          required
          hint="Whole units, e.g. 45000"
        />
        <Field
          label="Raised locally so far"
          name="alreadyRaised"
          hint="What the community has already collected."
        />
      </Section>

      <Section
        title="4. Documents"
        hint={`The first three are required. ${ACCEPTED_DESCRIPTION}.`}
        columns={1}
      >
        {FILE_KINDS.map((kind) => (
          <label key={kind.kind} className="block rounded-xl border border-sand-200 bg-white p-4">
            <span className="text-sm font-medium">
              {kind.label}
              {kind.required ? (
                <span className="ml-2 rounded bg-masjid-100 px-1.5 py-0.5 text-xs text-masjid-700">
                  required
                </span>
              ) : (
                <span className="ml-2 text-xs text-sand-700">optional</span>
              )}
            </span>
            <span className="mt-0.5 block text-xs text-sand-700">{kind.hint}</span>
            <input
              type="file"
              name={`file_${kind.kind}`}
              accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
              multiple={kind.kind === "site_photo"}
              className="mt-2 block w-full text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-masjid-700 file:px-4 file:py-2 file:font-semibold file:text-white hover:file:bg-masjid-800"
            />
          </label>
        ))}
      </Section>

      <Section title="5. Who we speak to" hint="One person on the committee who can answer questions.">
        <Field label="Full name" name="contactName" required />
        <Field label="Role on the committee" name="contactRole" required placeholder="Chairman, secretary, imam" />
        <Field label="Email" name="contactEmail" type="email" required />
        <Field label="Phone" name="contactPhone" required placeholder="+254…" />
      </Section>

      <Section
        title="6. Tell us about the community"
        hint="Where people pray now, what is wrong with it, who the masjid will serve, and what stage the build has reached."
        columns={1}
      >
        <textarea
          name="story"
          rows={8}
          required
          className="w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
        />
      </Section>

      <Section title="7. Declarations" columns={1}>
        <label className="flex items-start gap-3 text-sm">
          <input
            type="checkbox"
            name="consentTruthful"
            className="mt-0.5 h-4 w-4 rounded border-sand-300 text-masjid-700"
          />
          <span>
            Everything I have entered is true, and the documents attached are genuine copies.
          </span>
        </label>
        <label className="flex items-start gap-3 text-sm">
          <input
            type="checkbox"
            name="consentPublish"
            className="mt-0.5 h-4 w-4 rounded border-sand-300 text-masjid-700"
          />
          <span>
            If the application is approved, Masjid Fund may publish the project details, costs and
            build photographs to raise funds for it. Your documents and contact details are never
            published.
          </span>
        </label>
      </Section>

      <div className="rounded-2xl border border-sand-200 bg-white p-6">
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-xl bg-masjid-700 px-6 py-4 text-base font-semibold text-white transition hover:bg-masjid-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? "Uploading your documents…" : "Submit application"}
        </button>
        <p className="mt-3 text-center text-xs text-sand-700">
          You will get a reference and a link to track progress. Nothing is published while we
          review it.
        </p>
      </div>
    </form>
  );
}

function Section({
  title,
  hint,
  columns = 2,
  children,
}: {
  title: string;
  hint?: string;
  columns?: 1 | 2;
  children: React.ReactNode;
}) {
  return (
    <fieldset>
      <legend className="font-display text-lg font-semibold">{title}</legend>
      {hint && <p className="mt-1 text-sm text-sand-700">{hint}</p>}
      <div className={`mt-4 grid gap-4 ${columns === 2 ? "sm:grid-cols-2" : ""}`}>{children}</div>
    </fieldset>
  );
}

function Field({
  label,
  name,
  type = "text",
  required,
  hint,
  placeholder,
}: {
  label: string;
  name: string;
  type?: string;
  required?: boolean;
  hint?: string;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium">
        {label}
        {!required && <span className="ml-1 text-sand-700">(optional)</span>}
      </span>
      <input
        name={name}
        type={type}
        required={required}
        placeholder={placeholder}
        className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
      />
      {hint && <span className="mt-1 block text-xs text-sand-700">{hint}</span>}
    </label>
  );
}
