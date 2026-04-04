import { useMutation, useQueryClient } from "@tanstack/react-query";

import { logout } from "../api";

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(["me"], null);
      window.location.href = "/";
    },
  });
}
