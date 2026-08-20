import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getSession,
  login,
  logout,
  selectMerchant,
} from "@/features/auth/api/auth";

export const sessionQueryKey = ["auth", "session"] as const;

export function useSession() {
  return useQuery({ queryKey: sessionQueryKey, queryFn: getSession });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: login,
    onSuccess: (session) => queryClient.setQueryData(sessionQueryKey, session),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.clear();
      queryClient.setQueryData(sessionQueryKey, {
        authenticated: false,
        selected_merchant: null,
      });
    },
  });
}

export function useSelectMerchant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: selectMerchant,
    onSuccess: (session) => {
      queryClient.removeQueries({ queryKey: ["merchant-data"] });
      queryClient.setQueryData(sessionQueryKey, session);
    },
  });
}
