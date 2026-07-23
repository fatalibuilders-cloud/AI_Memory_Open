"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function NewProjectButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function create() {
    setBusy(true);
    const res = await fetch("/api/projects", { method: "POST" }).catch(() => null);
    setBusy(false);
    if (!res?.ok) return;
    const { project } = await res.json();
    router.push(`/projects/${project.id}/edit`);
  }

  return (
    <button
      onClick={create}
      disabled={busy}
      className="rounded-lg bg-amber-700 px-4 py-2.5 font-medium text-white hover:bg-amber-800 disabled:opacity-60"
    >
      {busy ? "Creating…" : "+ New project"}
    </button>
  );
}
