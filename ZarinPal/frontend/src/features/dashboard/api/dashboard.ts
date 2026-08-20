import { apiFetch } from "@/api/client";
import type {
  BenchmarkResponse,
  DashboardOverview,
  TransactionDetail,
  TransactionListResponse,
} from "@/features/dashboard/types";

export function getOverview(query: string) {
  return apiFetch<DashboardOverview>(`/api/dashboard/overview${query}`);
}

export function getBenchmarks(query: string) {
  return apiFetch<BenchmarkResponse>(`/api/dashboard/benchmarks${query}`);
}

export function getTransactions(query: string) {
  return apiFetch<TransactionListResponse>(`/api/transactions${query}`);
}

export function getTransaction(sessionKey: string) {
  return apiFetch<TransactionDetail>(
    `/api/transactions/${encodeURIComponent(sessionKey)}`,
  );
}
