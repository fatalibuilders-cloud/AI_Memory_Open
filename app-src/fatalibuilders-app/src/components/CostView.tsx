import { formatKES, type CostResult } from "@/engines/cost";

export function CostView({ result }: { result: CostResult }) {
  return (
    <section className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold">Cost estimate</h2>
        <p className="mt-1 text-xs text-stone-500">
          Fatali Builders 2026 rate card · cost engine v{result.engineVersion}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-xl border-2 border-amber-600 bg-white p-4 text-center">
          <p className="text-xs font-medium uppercase tracking-wide text-stone-500">
            Full contract (labour + materials)
          </p>
          <p className="mt-1 text-2xl font-bold">{formatKES(result.grandTotalFull)}</p>
          <p className="text-xs text-stone-500">incl. 5% contingency</p>
        </div>
        <div className="rounded-xl border border-stone-200 bg-white p-4 text-center">
          <p className="text-xs font-medium uppercase tracking-wide text-stone-500">
            Labour only (client supplies materials)
          </p>
          <p className="mt-1 text-2xl font-bold">{formatKES(result.grandTotalLabour)}</p>
          <p className="text-xs text-stone-500">incl. 5% contingency</p>
        </div>
      </div>

      {result.sections.map((sec) => (
        <details key={sec.title} className="rounded-xl border border-stone-200 bg-white">
          <summary className="flex cursor-pointer items-center justify-between px-4 py-3">
            <span className="font-semibold">{sec.title}</span>
            <span className="text-sm font-medium text-stone-600">
              {formatKES(sec.subtotalFull)}
            </span>
          </summary>
          <div className="overflow-x-auto border-t border-stone-100">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-stone-500">
                  <th className="px-4 py-2">Item</th>
                  <th className="px-2 py-2 text-right">Qty</th>
                  <th className="px-2 py-2">Unit</th>
                  <th className="px-2 py-2 text-right">Rate</th>
                  <th className="px-4 py-2 text-right">Amount</th>
                </tr>
              </thead>
              <tbody>
                {sec.items.map((i) => (
                  <tr key={i.label} className="border-t border-stone-50">
                    <td className="px-4 py-1.5">{i.label}</td>
                    <td className="px-2 py-1.5 text-right">{i.quantity}</td>
                    <td className="px-2 py-1.5">{i.unit}</td>
                    <td className="px-2 py-1.5 text-right">{i.rateFull.toLocaleString("en-KE")}</td>
                    <td className="px-4 py-1.5 text-right font-medium whitespace-nowrap">
                      {i.amountFull.toLocaleString("en-KE")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      ))}

      <div className="rounded-xl border border-stone-200 bg-white p-4 text-sm">
        <div className="flex justify-between py-1">
          <span>Measured works</span>
          <span className="font-medium">{formatKES(result.measuredWorksFull)}</span>
        </div>
        <div className="flex justify-between border-b border-stone-100 py-1">
          <span>Contingency (5%)</span>
          <span className="font-medium">{formatKES(result.contingencyFull)}</span>
        </div>
        <div className="flex justify-between py-2 text-base font-bold">
          <span>Grand total (full contract)</span>
          <span>{formatKES(result.grandTotalFull)}</span>
        </div>
      </div>

      <p className="rounded-lg bg-stone-100 px-4 py-3 text-xs text-stone-600">
        Estimate priced on the Fatali Builders 2026 rate card. Rates vary by region and market
        conditions — confirm current prices before contracting. This is a budgeting estimate, not
        a tender or a fixed quotation.
      </p>
    </section>
  );
}
