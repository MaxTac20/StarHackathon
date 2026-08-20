import { apiFetch } from "@/api/client";
import type { components } from "@/api/generated/schema";

export type SessionState = components["schemas"]["SessionResponse"];

export function getSession() {
  return apiFetch<SessionState>("/api/auth/session");
}

export function login(password: string) {
  return apiFetch<SessionState>("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
}

export async function logout() {
  await apiFetch<void>("/api/auth/logout", { method: "POST" });
}

export function selectMerchant(merchantKey: string) {
  return apiFetch<SessionState>("/api/auth/merchant", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ merchant_key: merchantKey }),
  });
}
