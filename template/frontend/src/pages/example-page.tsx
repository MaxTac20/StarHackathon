import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useHealth } from "@/features/example/hooks/use-health";

export function ExamplePage() {
  const health = useHealth();

  return (
    <section className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">
          End-to-end example
        </h1>
        <p className="mt-2 text-muted-foreground">
          This page uses TanStack Query to call FastAPI through the shared API
          client.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Backend health</CardTitle>
          <CardDescription>GET /api/health</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-between gap-4">
          <div aria-live="polite">
            {health.isPending && (
              <span className="text-muted-foreground">Checking…</span>
            )}
            {health.isError && (
              <span className="text-destructive">Unavailable</span>
            )}
            {health.data && (
              <span className="inline-flex items-center gap-2 font-medium">
                <span className="size-2 rounded-full bg-emerald-500" />
                API status: {health.data.status}
              </span>
            )}
          </div>
          <Button variant="outline" size="sm" onClick={() => health.refetch()}>
            <RefreshCw /> Refresh
          </Button>
        </CardContent>
      </Card>
    </section>
  );
}
