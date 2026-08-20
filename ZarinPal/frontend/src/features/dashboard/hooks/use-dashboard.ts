import { useQuery } from "@tanstack/react-query";
import {
  getBenchmarks,
  getOverview,
  getTransaction,
  getTransactions,
} from "@/features/dashboard/api/dashboard";

export function useOverview(query: string) {
  return useQuery({
    queryKey: ["merchant-data", "dashboard", query],
    queryFn: () => getOverview(query),
  });
}

export function useBenchmarks(query: string, enabled: boolean) {
  return useQuery({
    queryKey: ["merchant-data", "benchmarks", query],
    queryFn: () => getBenchmarks(query),
    enabled,
  });
}

export function useTransactions(query: string) {
  return useQuery({
    queryKey: ["merchant-data", "transactions", query],
    queryFn: () => getTransactions(query),
  });
}

export function useTransaction(sessionKey: string | null) {
  return useQuery({
    queryKey: ["merchant-data", "transaction", sessionKey],
    queryFn: () => getTransaction(sessionKey ?? ""),
    enabled: Boolean(sessionKey),
  });
}
