import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getProfile, updateEmail, updatePhone } from "./api";

export function useProfile() {
  const client = useQueryClient();
  const profile = useQuery({ queryKey: ["profile"], queryFn: getProfile, retry: false, gcTime: 0 });
  const changePhone = useMutation({
    mutationFn: updatePhone,
    onSuccess(result) {
      client.setQueryData(["profile"], result);
    },
  });
  const changeEmail = useMutation({
    mutationFn: updateEmail,
    onSuccess(result) {
      client.setQueryData(["profile"], result);
    },
  });
  return { profile, changePhone, changeEmail };
}
