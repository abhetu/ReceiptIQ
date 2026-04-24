import { NavLink } from "react-router-dom";

const navItems = [
  { label: "Dashboard", to: "/" },
  { label: "Uploads", to: "/uploads" },
  { label: "Reconciliation", to: "/reconciliation" },
  { label: "Reports", to: "/reports" },
];

export default function Sidebar() {
  return (
    <aside className="w-full lg:w-64 rounded-2xl bg-white p-4 shadow-soft">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">Navigation</h2>
      <nav className="space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `block rounded-xl px-3 py-2 text-sm font-medium ${
                isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
