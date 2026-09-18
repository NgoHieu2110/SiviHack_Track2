import type { CompanyProfile, TenderMatch } from "./tender-types"

/**
 * Central API layer between the frontend and the backend.
 *
 * POST /tenders/match no longer returns a single JSON response -- it
 * streams Server-Sent Events (text/event-stream) while the backend runs
 * its live pipeline (save profile -> build filter -> fetch tenders ->
 * Gemini selection). Each line is `data: {...}\n\n`, one of:
 *   {"type": "progress", "stage": "...", "message": "..."}   (many)
 *   {"type": "done", "matches": TenderMatch[]}                 (one, on success)
 *   {"type": "error", "message": "..."}                        (one, on failure)
 *
 * matchTendersRequest() reads that stream, optionally reporting progress
 * via onProgress, and resolves with the matches from the "done" event.
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

export type MatchProgressEvent = {
  type: "progress"
  stage: string
  message: string
}

type DoneEvent = { type: "done"; matches: TenderMatch[] }
type ErrorEvent = { type: "error"; message: string }
type StreamEvent = MatchProgressEvent | DoneEvent | ErrorEvent

/**
 * Send the company profile to the backend and stream back progress while
 * it runs, resolving with the matched tenders once the pipeline finishes.
 *
 * If NEXT_PUBLIC_API_BASE_URL isn't set, there is no local mock fallback
 * anymore -- the backend is required. (Bring back a mock branch here if
 * you still want offline UI development without the backend running.)
 */
export async function matchTendersRequest(
  profile: CompanyProfile,
  onProgress?: (event: MatchProgressEvent) => void,
  signal?: AbortSignal,
): Promise<TenderMatch[]> {
  if (!API_BASE_URL) {
    throw new ApiError("NEXT_PUBLIC_API_BASE_URL is not set. Point it at your backend, e.g. http://localhost:8000.")
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
    throw new ApiError(`Tender matching request failed (${response.status}).`, response.status)
  }
  if (!response.body) {
    throw new ApiError("Tender matching service returned no response body.")
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // SSE events are separated by a blank line ("\n\n").
    let separatorIndex: number
    while ((separatorIndex = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, separatorIndex)
      buffer = buffer.slice(separatorIndex + 2)

      const dataLine = rawEvent.split("\n").find((line) => line.startsWith("data:"))
      if (!dataLine) continue

      let event: StreamEvent
      try {
        event = JSON.parse(dataLine.slice("data:".length).trim())
      } catch {
        continue // ignore malformed/partial lines
      }

      if (event.type === "progress") {
        onProgress?.(event)
      } else if (event.type === "done") {
        return event.matches
      } else if (event.type === "error") {
        throw new ApiError(event.message)
      }
    }
  }

  throw new ApiError("Tender matching service closed the connection before finishing.")
}