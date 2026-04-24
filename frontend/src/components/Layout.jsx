import Sidebar from "./Sidebar";

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-slate-100 p-4 lg:p-6">
      <header className="mb-4 rounded-2xl bg-white p-4 shadow-soft">
        <h1 className="text-xl font-semibold text-slate-900">Receipt Reconciliation Agent</h1>
      </header>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[256px_1fr]">
        <Sidebar />
        <main className="space-y-4">{children}</main>
      </div>
    </div>
  );
}
