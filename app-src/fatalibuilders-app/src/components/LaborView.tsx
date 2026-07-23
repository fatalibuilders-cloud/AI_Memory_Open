import { formatKES } from "@/engines/cost";
import type { LaborResult } from "@/engines/labor";

const ROLE_LABELS: Record<string, string> = {
  mason: "Mason",
  laborer: "Laborer",
  carpenter: "Carpenter",
  painter: "Painter",
  engineer: "Engineer",
};

export function LaborView({ result }: { result: LaborResult }) {
  return (
    <section className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold">Labor & time plan</h2>
        <p className="mt-1 text-xs text-stone-500">
          Day rates: Fatali Builders site records · labor engine v{result.engineVersion}
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-xl border border-stone-200 bg-white p-3 text-center">
          <p className="text-xs font-medium uppercase tracking-wide text-stone-500">Duration</p>
          <p className="mt-1 text-lg font-bold">≈ {result.calendarWeeks} weeks</p>
          <p className="text-xs text-stone-500">{result.workingDays} working days</p>
        </div>
        <div className="rounded-xl border border-stone-200 bg-white p-3 text-center">
          <p className="text-xs font-medium uppercase tracking-wide text-stone-500">Peak crew</p>
          <p className="mt-1 text-lg font-bold">{result.peakCrew} people</p>
          <p className="text-xs text-stone-500">largest phase team</p>
        </div>
        <div className="rounded-xl border border-stone-200 bg-white p-3 text-center">
          <p className="text-xs font-medium uppercase tracking-wide text-stone-500">Labor cost</p>
          <p className="mt-1 text-lg font-bold">{formatKES(result.totalLaborCostKES)}</p>
          <p className="text-xs text-stone-500">incl. supervision</p>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-stone-200 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-stone-500">
              <th className="px-4 py-2">Phase</th>
              <th className="px-2 py-2">Crew</th>
              <th className="px-2 py-2 text-right">Days</th>
              <th className="px-4 py-2 text-right">Labor cost</th>
            </tr>
          </thead>
          <tbody>
            {result.phases.map((p) => (
              <tr key={p.name} className="border-t border-stone-50">
                <td className="px-4 py-2 font-medium">{p.name}</td>
                <td className="px-2 py-2 text-stone-600">
                  {p.crew.map((c) => `${c.count} ${ROLE_LABELS[c.role]}`).join(" + ")}
                </td>
                <td className="px-2 py-2 text-right">{p.durationDays}</td>
                <td className="px-4 py-2 text-right whitespace-nowrap">
                  {p.laborCostKES.toLocaleString("en-KE")}
                </td>
              </tr>
            ))}
            <tr className="border-t border-stone-100">
              <td className="px-4 py-2 font-medium">Supervision (engineer)</td>
              <td className="px-2 py-2 text-stone-600">1 Engineer, weekly</td>
              <td className="px-2 py-2 text-right">{result.supervisionDays}</td>
              <td className="px-4 py-2 text-right whitespace-nowrap">
                {(result.supervisionDays * result.dayRates.engineer).toLocaleString("en-KE")}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p className="rounded-lg bg-stone-100 px-4 py-3 text-xs text-stone-600">
        Durations assume phases overlap ~15% on a well-run site and a 6-day working week.
        Weather, deliveries and site conditions affect real timelines — use this as a planning
        baseline.
      </p>
    </section>
  );
}
