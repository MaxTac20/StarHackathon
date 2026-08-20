import { ArrowRight, Boxes, Route, Server } from "lucide-react";
import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const capabilities = [
  [
    Server,
    "One production app",
    "FastAPI serves the API and the compiled React application.",
  ],
  [
    Route,
    "Same-origin API",
    "Relative /api URLs work in development and production.",
  ],
  [
    Boxes,
    "Small by design",
    "Clear extension points without speculative abstraction layers.",
  ],
] as const;

export function HomePage() {
  return (
    <div className="space-y-12">
      <section className="max-w-3xl space-y-6">
        <p className="text-sm font-medium text-primary">
          FastAPI + React + PostgreSQL
        </p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
          Start building the product, not the scaffolding.
        </h1>
        <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
          A deliberately boring full-stack baseline for hackathons, MVPs, and
          real applications.
        </p>
        <Button asChild>
          <Link to="/example">
            Try the API example <ArrowRight />
          </Link>
        </Button>
      </section>
      <section className="grid gap-4 md:grid-cols-3">
        {capabilities.map(([Icon, title, description]) => (
          <Card key={title}>
            <CardHeader>
              <Icon className="size-5 text-primary" />
              <CardTitle>{title}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>{description}</CardDescription>
            </CardContent>
          </Card>
        ))}
      </section>
    </div>
  );
}
