import { apiClient } from "@/api/client"

export type HealthResponse = {
  status: string
  app: string
}

/** Example feature API module — replace/extend as real domains land. */
export function getHealth() {
  return apiClient<HealthResponse>("/api/v1/health")
}
