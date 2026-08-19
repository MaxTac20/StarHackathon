import { Outlet } from "react-router";
import { AppHeader } from "@/components/common/app-header";

export function RootLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppHeader />
      <main className="mx-auto max-w-5xl px-6 py-16">
        <Outlet />
      </main>
    </div>
  );
}
