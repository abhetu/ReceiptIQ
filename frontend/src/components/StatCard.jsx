export default function StatCard({ label, value, tone = "default" }) {
  const toneClasses = {
    default: "text-slate-900",
    matched: "text-emerald-600",
    flagged: "text-amber-600",
    unmatched: "text-rose-600",
  };

  return (
    <div className="rounded-2xl bg-white p-4 shadow-soft">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${toneClasses[tone] || toneClasses.default}`}>{value}</p>
    </div>
  );
}
