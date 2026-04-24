import { useState } from "react";
import { runReconciliation, confirmMatch, rejectMatch } from "../api";
import MatchTable from "../components/MatchTable";
import FlaggedMatchCard from "../components/FlaggedMatchCard";

export default function ReconciliationPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const run = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await runReconciliation();
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <button
        type="button"
        className="rounded-2xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-50"
        onClick={run}
        disabled={loading}
      >
        {loading ? "Running..." : "Run Reconciliation"}
      </button>

      {error && <div className="rounded-2xl bg-white p-4 text-rose-600 shadow-soft">{error}</div>}

      {data && (
        <>
          <MatchTable title="Matched" matches={data.matched} />

          <section className="space-y-3 rounded-2xl bg-white p-4 shadow-soft">
            <h3 className="text-lg font-semibold text-slate-900">Flagged Review</h3>
            {(data.flagged || []).map((item, idx) => (
              <FlaggedMatchCard
                key={`${item.receipt?.id || idx}-${item.transaction?.id || idx}`}
                item={item}
                onConfirm={() => confirmMatch(item.match_id).catch((e) => window.alert(e.message))}
                onReject={() => rejectMatch(item.match_id).catch((e) => window.alert(e.message))}
              />
            ))}
            {!data.flagged?.length && <p className="text-sm text-slate-500">No flagged matches.</p>}
          </section>

          <MatchTable title="Unmatched Receipts" matches={(data.unmatched_receipts || []).map((r) => ({ receipt: r, transaction: {}, score: 0 }))} />
          <MatchTable
            title="Unmatched Bank Transactions"
            matches={(data.unmatched_transactions || []).map((t) => ({ receipt: {}, transaction: t.transaction || t, score: 0 }))}
          />
        </>
      )}
    </div>
  );
}
