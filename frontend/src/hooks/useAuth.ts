import { useQuery } from "@tanstack/react-query";

import { getMe } from "../api";

export function useAuth() {
  const query = useQuery({
    queryKey: ["me"],
    queryFn: getMe,
    retry: false,
    staleTime: 1000 * 60 * 5,
  });

  return {
    user: query.data ?? null,
    isLoading: query.isLoading,
    isLoggedIn: Boolean(query.data),
    error: query.error,
  };
}
