import type { MaterialsResult } from "@/engines/materials/residential";
import { CODE_PROFILES, type CodeProfileId } from "@/engines/profiles";

export function ResultsView({
  result,
  codeProfile,
}: {
  result: MaterialsResult;
  codeProfile: CodeProfileId;
}) {
  const t = result.totals;
  const totalCards: Array<[string, string]> = [
    ["Cement", `${t.cementBags} bags`],
    ["Sand", `${t.sandM3} m³`],
    ["Ballast", `${t.ballastM3} m³`],
    ["Blocks", `${t.blocks}`],
    ["Steel", `${t.steelKg} kg`],
    ["BRC mesh", `${t.brcMeshM2} m²`],
    ...(t.roofCoverM2 > 0
      ? ([
          ["Roof cover", `${t.roofCoverM2} m²`],
          ["Roof timber", `${t.roofTimberM} m`],
        ] as Array<[string, string]>)
      : []),
    ...(t.paintLitres > 0 ? ([["Paint", `${t.paintLitres} L`]] as Array<[string, string]>) : []),
  ];

  return (
    <section className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold">Material quantities</h2>
        <p className="mt-1 text-xs text-stone-500">
          Code profile: {CODE_PROFILES[codeProfile].label} · engine v{result.engineVersion}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {totalCards.map(([label, value]) => (
          <div key={label} className="rounded-xl border border-stone-200 bg-white p-3 text-center">
            <p className="text-xs font-medium uppercase tracking-wide text-stone-500">{label}</p>
            <p className="mt-1 text-lg font-bold">{value}</p>
          </div>
        ))}
      </div>

      {result.sections.map((section) => (
        <details key={section.title} className="rounded-xl border border-stone-200 bg-white">
          <summary className="cursor-pointer px-4 py-3 font-semibold">{section.title}</summary>
          <table className="w-full border-t border-stone-100 text-sm">
            <tbody>
              {section.items.map((item) => (
                <tr key={item.label} className="border-b border-stone-50 last:border-0">
                  <td className="px-4 py-1.5">{item.label}</td>
                  <td className="px-4 py-1.5 text-right font-medium whitespace-nowrap">
                    {item.quantity} {item.unit}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      ))}

      <p className="rounded-lg bg-stone-100 px-4 py-3 text-xs text-stone-600">
        These are estimating quantities based on the {CODE_PROFILES[codeProfile].label} profile and
        stated assumptions — useful for budgeting and purchasing plans. Final quantities should be
        confirmed against detailed drawings. Engineering outputs always require review by a
        licensed engineer.
      </p>
    </section>
  );
}
