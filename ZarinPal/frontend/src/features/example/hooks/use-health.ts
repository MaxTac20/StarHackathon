import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/features/example/api/get-health";

export function useHealth() {
  return useQuery({ queryKey: ["health"], queryFn: getHealth });
}
