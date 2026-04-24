import { useEffect, useState } from "react";
import { getDashboard } from "../api";
import StatCard from "../components/StatCard";
import CategoryReport from "../components/CategoryReport";

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboard().then(setDashboard).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="rounded-2xl bg-white p-4 text-rose-600 shadow-soft">{error}</div>;
  if (!dashboard) return <div className="rounded-2xl bg-white p-4 text-slate-500 shadow-soft">Loading dashboard...</div>;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard label="Total Receipts" value={dashboard.total_receipts} />
        <StatCard label="Bank Transactions" value={dashboard.total_transactions} />
        <StatCard label="Matched" value={dashboard.matched_count} tone="matched" />
        <StatCard label="Needs Review" value={dashboard.flagged_count} tone="flagged" />
        <StatCard label="Unmatched" value={dashboard.unmatched_count} tone="unmatched" />
        <StatCard label="Total Spend" value={`$${Number(dashboard.total_spend || 0).toFixed(2)}`} />
      </div>
      <CategoryReport spendByCategory={dashboard.spend_by_category} />
    </div>
  );
}
