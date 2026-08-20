import { Link } from "react-router";
import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <section className="space-y-4 text-center">
      <p className="text-sm font-medium text-primary">404</p>
      <h1 className="text-4xl font-semibold">Page not found</h1>
      <Button asChild variant="outline">
        <Link to="/">Return home</Link>
      </Button>
    </section>
  );
}
