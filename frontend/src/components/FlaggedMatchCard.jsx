export default function FlaggedMatchCard({ item, onConfirm, onReject }) {
  const breakdown = item.score_breakdown || {};
  return (
    <div className="rounded-2xl border border-amber-200 bg-white p-4 shadow-soft">
      <div className="grid gap-2 text-sm text-slate-700 md:grid-cols-2">
        <div>
          <p className="font-semibold">Receipt</p>
          <p>{item.receipt?.vendor || "-"}</p>
          <p>{item.receipt?.date || "-"}</p>
          <p>${Number(item.receipt?.amount || 0).toFixed(2)}</p>
        </div>
        <div>
          <p className="font-semibold">Transaction</p>
          <p>{item.transaction?.description || "-"}</p>
          <p>{item.transaction?.txn_date || "-"}</p>
          <p>${Math.abs(Number(item.transaction?.amount || 0)).toFixed(2)}</p>
        </div>
      </div>
      <div className="mt-3 grid gap-2 rounded-xl bg-slate-50 p-3 text-sm md:grid-cols-3">
        <p>Score: <strong>{Math.round(item.score || 0)}</strong></p>
        <p>Confidence: <strong>{item.confidence || "LOW"}</strong></p>
        <p>
          Breakdown: A {Math.round(breakdown.amount || 0)} / D {Math.round(breakdown.date || 0)} / V {Math.round(breakdown.vendor || 0)}
        </p>
      </div>
      <p className="mt-2 text-sm text-slate-600">AI explanation: {item.explanation || "No explanation available."}</p>
      <div className="mt-3 flex gap-2">
        <button
          type="button"
          className="rounded-xl bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-500"
          onClick={onConfirm}
          disabled={!item.match_id}
        >
          Confirm
        </button>
        <button
          type="button"
          className="rounded-xl bg-rose-600 px-3 py-2 text-sm font-medium text-white hover:bg-rose-500"
          onClick={onReject}
          disabled={!item.match_id}
        >
          Reject
        </button>
      </div>
    </div>
  );
}
