import type { CompanyProfile, TenderMatch } from "./tender-types"
import { matchTenders } from "./tender-mock"

/**
 * Central API layer between the frontend and your backend.
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

/** One progress update streamed from the backend while it runs the tender pipeline. */
export type MatchProgressEvent = {
  type: "progress"
  /** Machine-readable pipeline stage, e.g. "fetching_tenders". */
  stage: string
  /** Human-readable message, safe to show directly in the UI. */
  message: string
}

type MatchDoneEvent = { type: "done"; matches: TenderMatch[] }
type MatchErrorEvent = { type: "error"; message: string }
type MatchStreamEvent = MatchProgressEvent | MatchDoneEvent | MatchErrorEvent

/**
 * Send the company profile to the backend and receive matched tenders back.
 *
 * The backend runs the full tender-search pipeline live and streams progress
 * back as Server-Sent Events on the same response body (a plain fetch +
 * ReadableStream reader is used instead of EventSource, since EventSource
 * can't send a POST body). Each progress update is reported via onProgress
 * as it arrives; the returned promise resolves once a final "done" event
 * carries the matched tenders.
 *
 * If no backend is configured, this resolves with mock results (after a
 * couple of simulated progress updates) so the frontend remains fully
 * functional during development.
 */
export async function matchTendersRequest(
  profile: CompanyProfile,
  onProgress?: (event: MatchProgressEvent) => void,
  signal?: AbortSignal,
): Promise<TenderMatch[]> {
  if (!API_BASE_URL) {
    onProgress?.({ type: "progress", stage: "mock", message: "Matching your profile against sample tenders..." })
    return new Promise((resolve) => setTimeout(() => resolve(matchTenders(profile)), 900))
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${MATCH_ENDPOINT}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify(profile),
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error
    throw new ApiError("Could not reach the tender matching service. Please try again.")
  }

  if (!response.ok) {
    throw new ApiError(`Tender matching request failed (${response.status}).`, response.status)
  }
  if (!response.body) {
    throw new ApiError("The tender matching service returned an empty response.")
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let matches: TenderMatch[] | null = null

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let separatorIndex: number
    // SSE events are separated by a blank line ("\n\n").
    while ((separatorIndex = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, separatorIndex)
      buffer = buffer.slice(separatorIndex + 2)

      const dataLine = rawEvent.split("\n").find((line) => line.startsWith("data:"))
      if (!dataLine) continue
      const jsonText = dataLine.slice(5).trim()
      if (!jsonText) continue

      let event: MatchStreamEvent
      try {
        event = JSON.parse(jsonText)
      } catch {
        continue
      }

      if (event.type === "progress") {
        onProgress?.(event)
      } else if (event.type === "done") {
        matches = event.matches
      } else if (event.type === "error") {
        throw new ApiError(event.message)
      }
    }
  }

  if (!matches) {
    throw new ApiError("Received an unexpected response from the tender matching service.")
  }

  return matches
}