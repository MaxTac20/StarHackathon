import { keepPreviousData, useQuery } from "@tanstack/react-query";
import {
  getMerchants,
  type MerchantListParams,
} from "@/features/merchants/api/get-merchants";

export function useMerchants(params: MerchantListParams) {
  return useQuery({
    queryKey: ["merchants", params],
    queryFn: () => getMerchants(params),
    placeholderData: keepPreviousData,
  });
}
