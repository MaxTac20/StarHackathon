import type { paths } from "@/api/generated/schema";
import { apiFetch } from "@/api/client";

export type HealthResponse =
  paths["/api/health"]["get"]["responses"][200]["content"]["application/json"];

export function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/health");
}
