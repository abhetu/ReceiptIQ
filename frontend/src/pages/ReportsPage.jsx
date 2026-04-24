import { useEffect, useState } from "react";
import { getReport } from "../api";
import CategoryReport from "../components/CategoryReport";

export default function ReportsPage() {
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getReport().then(setReport).catch((e) => setError(e.message));
  }, []);

  const exportCsv = () => {
    if (!report?.by_category) return;
    const rows = [["category", "count", "total"]];
    Object.entries(report.by_category).forEach(([category, value]) => {
      rows.push([category, String(value.count || 0), String(value.total || 0)]);
    });
    const csv = rows.map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "category-report.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (error) return <div className="rounded-2xl bg-white p-4 text-rose-600 shadow-soft">{error}</div>;
  if (!report) return <div className="rounded-2xl bg-white p-4 text-slate-500 shadow-soft">Loading report...</div>;

  const spendByCategory = Object.fromEntries(
    Object.entries(report.by_category || {}).map(([k, v]) => [k, v.total || 0])
  );

  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-white p-4 shadow-soft">
        <p className="text-sm text-slate-500">Grand Total</p>
        <p className="mt-1 text-2xl font-semibold text-slate-900">${Number(report.grand_total || 0).toFixed(2)}</p>
        <button
          type="button"
          className="mt-3 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
          onClick={exportCsv}
        >
          Export CSV
        </button>
      </div>
      <CategoryReport spendByCategory={spendByCategory} />
    </div>
  );
}
