import { formatMoney, progressPercent } from "@/lib/money";

export function ProgressBar({
  raisedCents,
  goalCents,
  compact = false,
}: {
  raisedCents: number;
  goalCents: number;
  compact?: boolean;
}) {
  const percent = progressPercent(raisedCents, goalCents);
  const remaining = Math.max(0, goalCents - raisedCents);

  return (
    <div>
      <div
        className="h-2.5 w-full overflow-hidden rounded-full bg-sand-200"
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${percent}% of the ${formatMoney(goalCents)} goal raised`}
      >
        <div
          className="h-full rounded-full bg-gradient-to-r from-masjid-600 to-masjid-500 transition-[width] duration-700"
          style={{ width: `${percent}%` }}
        />
      </div>
      <div
        className={`mt-2 flex flex-wrap items-baseline justify-between gap-x-3 ${
          compact ? "text-xs" : "text-sm"
        }`}
      >
        <p className="font-semibold text-masjid-900">
          {formatMoney(raisedCents)}{" "}
          <span className="font-normal text-sand-700">of {formatMoney(goalCents)}</span>
        </p>
        <p className="text-sand-700">
          {remaining === 0 ? "Fully funded" : `${formatMoney(remaining)} to go`}
        </p>
      </div>
    </div>
  );
}
