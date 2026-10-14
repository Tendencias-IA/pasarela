import type { components } from "../../shared/api/types.gen";
import { request } from "../../shared/api/client";

export type RegisterAccountInput = components["schemas"]["RegisterAccountRequest"];
export type RegisterAccountResponse = components["schemas"]["RegisterAccountResponse"];
export function registerAccount(input: RegisterAccountInput) {
  return request<RegisterAccountResponse>("/api/v1/accounts", {
    method: "POST",
    body: input,
  });
}

export type AccountProfile = components["schemas"]["AccountProfile"];
export function getProfile() {
  return request<AccountProfile>("/api/v1/profile");
}
export function updatePhone(phone: string) {
  return request<AccountProfile>("/api/v1/profile", { method: "PATCH", body: { phone } });
}
