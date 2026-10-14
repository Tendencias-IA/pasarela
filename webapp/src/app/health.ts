import { request } from "../shared/api/client";

export interface Health {
  status: "ok" | "degraded";
  db: "ok" | "error";
}

export function getHealth(signal?: AbortSignal): Promise<Health> {
  return request<Health>("/health", { signal });
}
