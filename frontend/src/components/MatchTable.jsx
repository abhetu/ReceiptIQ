export default function MatchTable({ title, matches = [] }) {
  return (
    <section className="rounded-2xl bg-white p-4 shadow-soft">
      <h3 className="mb-3 text-lg font-semibold text-slate-900">{title}</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="pb-2 pr-4">Vendor</th>
              <th className="pb-2 pr-4">Receipt Amount</th>
              <th className="pb-2 pr-4">Transaction</th>
              <th className="pb-2 pr-4">Txn Amount</th>
              <th className="pb-2 pr-4">Score</th>
            </tr>
          </thead>
          <tbody>
            {matches.map((item, idx) => (
              <tr key={`${item.receipt?.id || idx}-${item.transaction?.id || idx}`} className="border-t border-slate-100">
                <td className="py-2 pr-4">{item.receipt?.vendor || "-"}</td>
                <td className="py-2 pr-4">${Number(item.receipt?.amount || 0).toFixed(2)}</td>
                <td className="py-2 pr-4">{item.transaction?.description || "-"}</td>
                <td className="py-2 pr-4">${Math.abs(Number(item.transaction?.amount || 0)).toFixed(2)}</td>
                <td className="py-2 pr-4">{Math.round(item.score || 0)}</td>
              </tr>
            ))}
            {!matches.length && (
              <tr>
                <td className="py-4 text-slate-500" colSpan={5}>
                  No records yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
