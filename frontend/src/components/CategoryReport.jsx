export default function CategoryReport({ spendByCategory = {} }) {
  const entries = Object.entries(spendByCategory).sort((a, b) => b[1] - a[1]);
  const max = entries[0]?.[1] || 1;

  return (
    <section className="rounded-2xl bg-white p-4 shadow-soft">
      <h3 className="mb-3 text-lg font-semibold text-slate-900">Category Spend</h3>
      <div className="space-y-3">
        {entries.map(([category, amount]) => (
          <div key={category}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="text-slate-700">{category}</span>
              <span className="font-medium text-slate-900">${Number(amount || 0).toFixed(2)}</span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div className="h-2 rounded-full bg-slate-900" style={{ width: `${(amount / max) * 100}%` }} />
            </div>
          </div>
        ))}
        {!entries.length && <p className="text-sm text-slate-500">No category data available.</p>}
      </div>
    </section>
  );
}
