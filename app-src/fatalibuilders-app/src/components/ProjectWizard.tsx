"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  FLOOR_FINISHES,
  ROOF_TYPES,
  SOIL_TYPES,
  WALL_TYPES,
  type ProjectDraft,
  type ProjectRecord,
} from "@/lib/project-schema";

const STEPS = ["Basics", "Dimensions", "Structure & roof", "Openings & finishes", "Soil", "Review"];

const PROFILES = [
  { id: "eurocode", label: "Eurocodes (recommended)" },
  { id: "bs", label: "British Standards (BS)" },
  { id: "kebs", label: "Kenya (KEBS + Eurocode/BS practice)" },
] as const;

export function ProjectWizard({ project }: { project: ProjectRecord }) {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [name, setName] = useState(project.name);
  const [data, setData] = useState<ProjectDraft>({
    codeProfile: "eurocode",
    country: "Kenya",
    floors: 1,
    floorHeightM: 2.8,
    wallType: "concrete_block",
    wallThicknessMm: 200,
    roofType: "gable_iron_sheets",
    doorsCount: 6,
    windowsCount: 8,
    plasterBothSides: true,
    paint: true,
    floorFinish: "screed",
    soilType: "unknown",
    ...project.data,
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function set<K extends keyof ProjectDraft>(key: K, value: ProjectDraft[K]) {
    setData((d) => ({ ...d, [key]: value }));
  }

  async function save(status?: "complete"): Promise<boolean> {
    setBusy(true);
    setError(null);
    const res = await fetch(`/api/projects/${project.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, data, ...(status ? { status } : {}) }),
    }).catch(() => null);
    setBusy(false);
    if (!res) {
      setError("Network problem — your changes were not saved. Try again.");
      return false;
    }
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setError(body.error ?? "Could not save. Try again.");
      return false;
    }
    return true;
  }

  async function next() {
    if (await save()) setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  async function finish() {
    if (await save("complete")) {
      router.push(`/projects/${project.id}`);
      router.refresh();
    }
  }

  const input =
    "rounded-lg border border-stone-300 px-3 py-2 text-base focus:border-amber-600 focus:outline-none";
  const label = "flex flex-col gap-1 text-sm font-medium";

  return (
    <div className="flex flex-col gap-6">
      <ol className="flex flex-wrap gap-2 text-xs">
        {STEPS.map((s, i) => (
          <li
            key={s}
            className={`rounded-full px-3 py-1 ${
              i === step
                ? "bg-amber-700 text-white"
                : i < step
                  ? "bg-amber-100 text-amber-800"
                  : "bg-stone-100 text-stone-500"
            }`}
          >
            {i + 1}. {s}
          </li>
        ))}
      </ol>

      {step === 0 && (
        <div className="flex flex-col gap-4">
          <label className={label}>
            Project name
            <input className={input} value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label className={label}>
            Country
            <input
              className={input}
              value={data.country ?? ""}
              onChange={(e) => set("country", e.target.value)}
            />
          </label>
          <label className={label}>
            Design code profile
            <select
              className={input}
              value={data.codeProfile}
              onChange={(e) => set("codeProfile", e.target.value as ProjectDraft["codeProfile"])}
            >
              {PROFILES.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
            <span className="text-xs font-normal text-stone-500">
              The recognized set of engineering rules your results will follow. Every document
              states which profile produced it.
            </span>
          </label>
          <label className={label}>
            Number of floors (ground = 1)
            <input
              className={input}
              type="number"
              min={1}
              max={4}
              value={data.floors ?? 1}
              onChange={(e) => set("floors", Number(e.target.value))}
            />
          </label>
        </div>
      )}

      {step === 1 && (
        <div className="flex flex-col gap-4">
          <p className="text-sm text-stone-600">
            Measure the outside of the building footprint in metres.
          </p>
          <label className={label}>
            Building length (m)
            <input
              className={input}
              type="number"
              min={1}
              step="0.1"
              value={data.footprintLengthM ?? ""}
              onChange={(e) => set("footprintLengthM", Number(e.target.value))}
            />
          </label>
          <label className={label}>
            Building width (m)
            <input
              className={input}
              type="number"
              min={1}
              step="0.1"
              value={data.footprintWidthM ?? ""}
              onChange={(e) => set("footprintWidthM", Number(e.target.value))}
            />
          </label>
          <label className={label}>
            Floor-to-ceiling height (m)
            <input
              className={input}
              type="number"
              min={2.2}
              max={4.5}
              step="0.1"
              value={data.floorHeightM ?? 2.8}
              onChange={(e) => set("floorHeightM", Number(e.target.value))}
            />
          </label>
        </div>
      )}

      {step === 2 && (
        <div className="flex flex-col gap-4">
          <label className={label}>
            Wall material
            <select
              className={input}
              value={data.wallType}
              onChange={(e) => set("wallType", e.target.value as ProjectDraft["wallType"])}
            >
              {Object.entries(WALL_TYPES).map(([id, l]) => (
                <option key={id} value={id}>
                  {l}
                </option>
              ))}
            </select>
          </label>
          <label className={label}>
            Wall thickness (mm)
            <select
              className={input}
              value={data.wallThicknessMm ?? 200}
              onChange={(e) => set("wallThicknessMm", Number(e.target.value))}
            >
              {[150, 200, 230].map((t) => (
                <option key={t} value={t}>
                  {t} mm
                </option>
              ))}
            </select>
          </label>
          <label className={label}>
            Roof
            <select
              className={input}
              value={data.roofType}
              onChange={(e) => set("roofType", e.target.value as ProjectDraft["roofType"])}
            >
              {Object.entries(ROOF_TYPES).map(([id, l]) => (
                <option key={id} value={id}>
                  {l}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}

      {step === 3 && (
        <div className="flex flex-col gap-4">
          <label className={label}>
            Number of doors
            <input
              className={input}
              type="number"
              min={0}
              value={data.doorsCount ?? 6}
              onChange={(e) => set("doorsCount", Number(e.target.value))}
            />
          </label>
          <label className={label}>
            Number of windows
            <input
              className={input}
              type="number"
              min={0}
              value={data.windowsCount ?? 8}
              onChange={(e) => set("windowsCount", Number(e.target.value))}
            />
          </label>
          <label className="flex items-center gap-2 text-sm font-medium">
            <input
              type="checkbox"
              checked={data.plasterBothSides ?? true}
              onChange={(e) => set("plasterBothSides", e.target.checked)}
            />
            Plaster walls on both sides
          </label>
          <label className="flex items-center gap-2 text-sm font-medium">
            <input
              type="checkbox"
              checked={data.paint ?? true}
              onChange={(e) => set("paint", e.target.checked)}
            />
            Paint the walls
          </label>
          <label className={label}>
            Floor finish
            <select
              className={input}
              value={data.floorFinish}
              onChange={(e) => set("floorFinish", e.target.value as ProjectDraft["floorFinish"])}
            >
              {Object.entries(FLOOR_FINISHES).map(([id, l]) => (
                <option key={id} value={id}>
                  {l}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}

      {step === 4 && (
        <div className="flex flex-col gap-4">
          <label className={label}>
            Soil type at the site (if known)
            <select
              className={input}
              value={data.soilType}
              onChange={(e) => set("soilType", e.target.value as ProjectDraft["soilType"])}
            >
              {Object.entries(SOIL_TYPES).map(([id, l]) => (
                <option key={id} value={id}>
                  {l}
                </option>
              ))}
            </select>
            <span className="text-xs font-normal text-stone-500">
              Optional. If you know the soil type, the app can prepare a preliminary geotechnical
              report for this project in a future update — it always requires review by a licensed
              engineer.
            </span>
          </label>
        </div>
      )}

      {step === 5 && (
        <div className="flex flex-col gap-2 rounded-xl border border-stone-200 bg-white p-4 text-sm">
          <p className="font-semibold">{name}</p>
          <p>
            {data.country} · {data.floors} floor(s) · {data.footprintLengthM ?? "—"} ×{" "}
            {data.footprintWidthM ?? "—"} m · height {data.floorHeightM} m
          </p>
          <p>
            {WALL_TYPES[data.wallType ?? "concrete_block"]}, {data.wallThicknessMm} mm ·{" "}
            {ROOF_TYPES[data.roofType ?? "gable_iron_sheets"]}
          </p>
          <p>
            {data.doorsCount} doors · {data.windowsCount} windows ·{" "}
            {data.plasterBothSides ? "plastered" : "no plaster"} ·{" "}
            {data.paint ? "painted" : "no paint"} ·{" "}
            {FLOOR_FINISHES[data.floorFinish ?? "screed"]}
          </p>
          <p>Soil: {SOIL_TYPES[data.soilType ?? "unknown"]}</p>
          <p className="text-stone-500">
            Code profile: {PROFILES.find((p) => p.id === data.codeProfile)?.label}
          </p>
        </div>
      )}

      {error && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0 || busy}
          className="rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100 disabled:opacity-40"
        >
          ← Back
        </button>
        {step < STEPS.length - 1 ? (
          <button
            type="button"
            onClick={next}
            disabled={busy}
            className="rounded-lg bg-amber-700 px-5 py-2 font-medium text-white hover:bg-amber-800 disabled:opacity-60"
          >
            {busy ? "Saving…" : "Save & continue →"}
          </button>
        ) : (
          <button
            type="button"
            onClick={finish}
            disabled={busy}
            className="rounded-lg bg-green-700 px-5 py-2 font-medium text-white hover:bg-green-800 disabled:opacity-60"
          >
            {busy ? "Saving…" : "Finish project ✓"}
          </button>
        )}
      </div>
    </div>
  );
}
