import { apiFetch } from "@/api/client";
import type { components } from "@/api/generated/schema";

export type MerchantList = components["schemas"]["MerchantListResponse"];
export type MerchantSummary = components["schemas"]["MerchantSummary"];
export type MerchantSort = components["schemas"]["MerchantSort"];
export type SortDirection = components["schemas"]["SortDirection"];

export interface MerchantListParams {
  search: string;
  categoryId: string;
  sort: MerchantSort;
  direction: SortDirection;
  page: number;
  pageSize: number;
}

export function getMerchants(params: MerchantListParams) {
  const query = new URLSearchParams({
    sort: params.sort,
    direction: params.direction,
    page: String(params.page),
    page_size: String(params.pageSize),
  });
  if (params.search) query.set("search", params.search);
  if (params.categoryId) query.set("category_id", params.categoryId);
  return apiFetch<MerchantList>(`/api/merchants?${query.toString()}`);
}
