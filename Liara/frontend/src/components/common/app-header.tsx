import { Link, NavLink } from "react-router";
import { cn } from "@/lib/utils";

export function AppHeader() {
  return (
    <header className="border-b border-border bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-6">
        <Link to="/" className="font-semibold tracking-tight">
          Starter
        </Link>
        <nav aria-label="Main navigation" className="flex gap-5 text-sm">
          {[
            { to: "/", label: "Home" },
            { to: "/example", label: "Example" },
          ].map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                cn(
                  "text-muted-foreground hover:text-foreground",
                  isActive && "text-foreground",
                )
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
