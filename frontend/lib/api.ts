import type { CompanyProfile, TenderMatch } from "./tender-types"
import { matchTenders } from "./tender-mock"

/**
 * Central API layer between the frontend and your future backend.
 *
 * Set NEXT_PUBLIC_API_BASE_URL (e.g. https://api.yourdomain.com) to point the
 * app at a real backend. Until it is set, requests fall back to the local mock
 * matching engine so the UI keeps working during development.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? ""

/** Endpoint the profile is POSTed to. Adjust to match your backend routing. */
const MATCH_ENDPOINT = "/tenders/match"

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

/** Shape the backend is expected to return. */
type MatchTendersResponse = {
  matches: TenderMatch[]
}

/**
 * Send the company profile to the backend and receive matched tenders back.
 *
 * The backend is expected to accept the CompanyProfile as JSON and respond with
 * `{ matches: TenderMatch[] }`. If no backend is configured, this resolves with
 * mock results so the frontend remains fully functional.
 */
export async function matchTendersRequest(
  profile: CompanyProfile,
  signal?: AbortSignal,
): Promise<TenderMatch[]> {
  if (!API_BASE_URL) {
    // No backend configured yet — simulate a round-trip with the local mock.
    return new Promise((resolve) => setTimeout(() => resolve(matchTenders(profile)), 900))
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${MATCH_ENDPOINT}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error
    throw new ApiError("Could not reach the tender matching service. Please try again.")
  }

  if (!response.ok) {
    throw new ApiError(
      `Tender matching request failed (${response.status}).`,
      response.status,
    )
  }

  const data = (await response.json()) as MatchTendersResponse
  if (!data || !Array.isArray(data.matches)) {
    throw new ApiError("Received an unexpected response from the tender matching service.")
  }

  return data.matches
}
