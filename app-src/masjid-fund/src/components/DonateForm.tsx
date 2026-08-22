"use client";

import { useMemo, useState } from "react";
import {
  INTENTS,
  INTENT_LABELS,
  INTENT_NOTES,
  PRESET_AMOUNTS_CENTS,
  type Frequency,
  type Intent,
} from "@/lib/donation";
import {
  MAX_DONATION_CENTS,
  MIN_DONATION_CENTS,
  formatMoney,
  fromBase,
  parseAmountToCents,
} from "@/lib/money";

export interface DonateFormProject {
  slug: string;
  name: string;
  city: string;
  country: string;
}

const DEFAULT_AMOUNT_CENTS = 10000;

export function DonateForm({
  projects,
  defaultProjectSlug = "",
  defaultFrequency = "one_time",
  defaultAmountCents = DEFAULT_AMOUNT_CENTS,
  liveMode,
  methods = [{ value: "card", label: "Card", hint: "Visa, Mastercard, Apple Pay" }],
}: {
  projects: DonateFormProject[];
  defaultProjectSlug?: string;
  defaultFrequency?: Frequency;
  /** Pre-selected amount, e.g. when a donor picks a costed item on a project page. */
  defaultAmountCents?: number;
  /** False when payments run through the built-in simulator. */
  liveMode: boolean;
  /** Rails this deployment can take money on, in the order they are offered. */
  methods?: { value: "card" | "mpesa"; label: string; hint: string }[];
}) {
  const [amountCents, setAmountCents] = useState<number | null>(defaultAmountCents);
  // An amount that is not one of the presets starts life in the custom field.
  const [customAmount, setCustomAmount] = useState(() =>
    PRESET_AMOUNTS_CENTS.includes(defaultAmountCents)
      ? ""
      : (defaultAmountCents / 100).toFixed(defaultAmountCents % 100 === 0 ? 0 : 2),
  );
  const [frequency, setFrequency] = useState<Frequency>(defaultFrequency);
  const [intent, setIntent] = useState<Intent>("sadaqah_jariyah");
  const [projectSlug, setProjectSlug] = useState(defaultProjectSlug);
  const [donorName, setDonorName] = useState("");
  const [donorEmail, setDonorEmail] = useState("");
  const [anonymous, setAnonymous] = useState(false);
  const [dedication, setDedication] = useState("");
  const [message, setMessage] = useState("");
  const [method, setMethod] = useState<"card" | "mpesa">(methods[0]?.value ?? "card");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const zakat = intent === "zakat";
  const mpesa = method === "mpesa";
  const selectedProject = useMemo(
    () => projects.find((p) => p.slug === projectSlug) ?? null,
    [projects, projectSlug],
  );

  function chooseCustom(value: string) {
    setCustomAmount(value);
    setAmountCents(parseAmountToCents(value));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    if (amountCents === null) {
      setError("Enter a donation amount, for example 50 or 125.50.");
      return;
    }
    if (amountCents < MIN_DONATION_CENTS) {
      setError(`The smallest donation we can process is ${formatMoney(MIN_DONATION_CENTS)}.`);
      return;
    }
    if (amountCents > MAX_DONATION_CENTS) {
      setError(
        `For gifts above ${formatMoney(MAX_DONATION_CENTS)}, email us and we will arrange a transfer.`,
      );
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("/api/donations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          method,
          phone,
          amountCents,
          projectSlug: zakat || !projectSlug ? null : projectSlug,
          frequency,
          intent,
          donorName,
          donorEmail,
          anonymous,
          dedication,
          message,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.error ?? "We could not start this donation. Please try again.");
        setSubmitting(false);
        return;
      }
      window.location.href = data.checkoutUrl;
    } catch {
      setError("Network problem — check your connection and try again.");
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8" noValidate>
      {!liveMode && (
        <p className="rounded-xl border border-brass-400 bg-brass-400/10 px-4 py-3 text-sm text-sand-800">
          <strong className="font-semibold">Test mode.</strong> No payment provider is
          configured, so checkout is simulated and no money moves.
        </p>
      )}

      <fieldset>
        <legend className="font-display text-lg font-semibold">1. Choose your gift</legend>

        <div className="mt-4 inline-flex rounded-xl border border-sand-200 bg-white p-1">
          {(["one_time", "monthly"] as Frequency[]).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => {
                setFrequency(value);
                if (value === "monthly" && mpesa) setMethod("card");
              }}
              aria-pressed={frequency === value}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                frequency === value
                  ? "bg-masjid-700 text-white"
                  : "text-masjid-800 hover:bg-sand-100"
              }`}
            >
              {value === "one_time" ? "Give once" : "Give monthly"}
            </button>
          ))}
        </div>

        <div className="mt-4 grid grid-cols-3 gap-2 sm:grid-cols-6">
          {PRESET_AMOUNTS_CENTS.map((cents) => (
            <button
              key={cents}
              type="button"
              onClick={() => {
                setAmountCents(cents);
                setCustomAmount("");
              }}
              aria-pressed={amountCents === cents && customAmount === ""}
              className={`rounded-xl border px-3 py-3 text-sm font-semibold transition ${
                amountCents === cents && customAmount === ""
                  ? "border-masjid-700 bg-masjid-50 text-masjid-800 ring-1 ring-masjid-700"
                  : "border-sand-200 bg-white hover:border-masjid-200"
              }`}
            >
              {formatMoney(cents)}
            </button>
          ))}
        </div>

        <label className="mt-4 block">
          <span className="text-sm font-medium">Or enter another amount</span>
          <div className="mt-1 flex items-center rounded-xl border border-sand-200 bg-white focus-within:ring-2 focus-within:ring-masjid-500">
            <span className="pl-3 text-sand-700">$</span>
            <input
              inputMode="decimal"
              value={customAmount}
              onChange={(e) => chooseCustom(e.target.value)}
              placeholder="250"
              className="w-full bg-transparent px-2 py-3 outline-none"
              aria-label="Custom donation amount in US dollars"
            />
          </div>
        </label>
      </fieldset>

      <fieldset>
        <legend className="font-display text-lg font-semibold">2. Where it goes</legend>

        <label className="mt-4 block">
          <span className="text-sm font-medium">Masjid project</span>
          <select
            value={zakat ? "" : projectSlug}
            disabled={zakat}
            onChange={(e) => setProjectSlug(e.target.value)}
            className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500 disabled:opacity-60"
          >
            <option value="">Where it is needed most</option>
            {projects.map((project) => (
              <option key={project.slug} value={project.slug}>
                {project.name} — {project.city}, {project.country}
              </option>
            ))}
          </select>
        </label>

        <div className="mt-4">
          <span className="text-sm font-medium">Type of giving</span>
          <div className="mt-2 grid gap-2 sm:grid-cols-3">
            {INTENTS.map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setIntent(value)}
                aria-pressed={intent === value}
                className={`rounded-xl border px-3 py-3 text-sm font-semibold transition ${
                  intent === value
                    ? "border-masjid-700 bg-masjid-50 text-masjid-800 ring-1 ring-masjid-700"
                    : "border-sand-200 bg-white hover:border-masjid-200"
                }`}
              >
                {INTENT_LABELS[value]}
              </button>
            ))}
          </div>
          <p className="mt-2 text-sm leading-relaxed text-sand-700">{INTENT_NOTES[intent]}</p>
        </div>
      </fieldset>


      <fieldset>
        <legend className="font-display text-lg font-semibold">3. How you will pay</legend>

        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {methods.map((option) => {
            const unavailable = option.value === "mpesa" && frequency === "monthly";
            return (
              <button
                key={option.value}
                type="button"
                disabled={unavailable}
                onClick={() => setMethod(option.value)}
                aria-pressed={method === option.value}
                className={`rounded-xl border px-4 py-3 text-left transition disabled:cursor-not-allowed disabled:opacity-50 ${
                  method === option.value
                    ? "border-masjid-700 bg-masjid-50 ring-1 ring-masjid-700"
                    : "border-sand-200 bg-white hover:border-masjid-200"
                }`}
              >
                <span className="block font-semibold">{option.label}</span>
                <span className="mt-0.5 block text-xs text-sand-700">
                  {unavailable ? "Not available for monthly giving" : option.hint}
                </span>
              </button>
            );
          })}
        </div>

        {mpesa && (
          <label className="mt-4 block">
            <span className="text-sm font-medium">M-Pesa number</span>
            <input
              inputMode="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="0722 000 000"
              className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
            />
            <span className="mt-1 block text-xs text-sand-700">
              We send a prompt to this number and you enter your M-Pesa PIN. Charged in shillings:
              {" "}
              {amountCents ? formatMoney(fromBase(amountCents, "KES"), "KES") : "—"}.
            </span>
          </label>
        )}
      </fieldset>

      <fieldset>
        <legend className="font-display text-lg font-semibold">4. Your details</legend>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="text-sm font-medium">Name</span>
            <input
              value={donorName}
              onChange={(e) => setDonorName(e.target.value)}
              autoComplete="name"
              className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium">
              Email <span className="text-sand-700">(for your receipt)</span>
            </span>
            <input
              type="email"
              required
              value={donorEmail}
              onChange={(e) => setDonorEmail(e.target.value)}
              autoComplete="email"
              className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
            />
          </label>
        </div>

        <label className="mt-4 block">
          <span className="text-sm font-medium">
            Dedicate this gift <span className="text-sand-700">(optional)</span>
          </span>
          <input
            value={dedication}
            onChange={(e) => setDedication(e.target.value)}
            placeholder="On behalf of my late father, rahimahu Allah"
            className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
          />
        </label>

        <label className="mt-4 block">
          <span className="text-sm font-medium">
            Message to the community <span className="text-sand-700">(optional)</span>
          </span>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={3}
            className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
          />
        </label>

        <label className="mt-4 flex items-start gap-3 text-sm">
          <input
            type="checkbox"
            checked={anonymous}
            onChange={(e) => setAnonymous(e.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-sand-300 text-masjid-700 focus:ring-masjid-500"
          />
          <span>Give anonymously — your name will not appear anywhere public.</span>
        </label>
      </fieldset>

      <div className="rounded-2xl border border-sand-200 bg-white p-5">
        <p className="text-sm text-sand-700">Summary</p>
        <p className="mt-1 font-display text-lg">
          {amountCents
            ? mpesa
              ? `${formatMoney(fromBase(amountCents, "KES"), "KES")} (${formatMoney(amountCents)})`
              : formatMoney(amountCents)
            : "—"}
          {frequency === "monthly" ? " each month" : ""} as {INTENT_LABELS[intent].toLowerCase()}
          {zakat
            ? ", held separately for eligible recipients"
            : selectedProject
              ? ` towards ${selectedProject.name}`
              : " where it is needed most"}
          .
        </p>

        {error && (
          <p role="alert" className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="mt-5 w-full rounded-xl bg-masjid-700 px-6 py-4 text-base font-semibold text-white transition hover:bg-masjid-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? "Taking you to checkout…" : "Continue to secure payment"}
        </button>
        <p className="mt-3 text-center text-xs text-sand-700">
          Card details are entered on the payment provider&apos;s page — they never touch our
          servers.
        </p>
      </div>
    </form>
  );
}
