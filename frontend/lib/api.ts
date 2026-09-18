import type { CompanyProfile, TenderMatch } from "./tender-types"

/**
 * Central API layer between the frontend and the backend.
 *
 * POST /tenders/match no longer returns a single JSON response -- it
 * streams Server-Sent Events (text/event-stream) while the backend runs
 * its live pipeline (save profile -> build filter -> fetch tenders ->
 * Claude selection). Each line is `data: {...}\n\n`, one of:
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

type DoneEvent = { type: "done"; [key: string]: unknown }
type ErrorEvent = { type: "error"; message: string }
type StreamEvent = MatchProgressEvent | DoneEvent | ErrorEvent

/**
 * POST `body` to `path` and read back a `text/event-stream` response shaped
 * like main.py's three pipeline routes (/tenders/match, /tenders/remove,
 * /tenders/refine): many `{"type": "progress", ...}` lines, then one
 * `{"type": "done", ...}` or `{"type": "error", "message": "..."}` line.
 * Reports progress via `onProgress` and resolves with the "done" event
 * (including its "type" field -- callers destructure what they need).
 */
async function streamPipelineRequest(
  path: string,
  body: unknown,
  onProgress: ((event: MatchProgressEvent) => void) | undefined,
  signal: AbortSignal | undefined,
  serviceLabel: string,
): Promise<DoneEvent> {
  if (!API_BASE_URL) {
    throw new ApiError("NEXT_PUBLIC_API_BASE_URL is not set. Point it at your backend, e.g. http://localhost:8000.")
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error
    throw new ApiError(`Could not reach ${serviceLabel}. Please try again.`)
  }

  if (!response.ok) {
    throw new ApiError(`${serviceLabel} request failed (${response.status}).`, response.status)
  }
  if (!response.body) {
    throw new ApiError(`${serviceLabel} returned no response body.`)
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
        return event
      } else if (event.type === "error") {
        throw new ApiError(event.message)
      }
    }
  }

  throw new ApiError(`${serviceLabel} closed the connection before finishing.`)
}

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
  const event = await streamPipelineRequest(
    MATCH_ENDPOINT,
    profile,
    onProgress,
    signal,
    "the tender matching service",
  )
  return event.matches as TenderMatch[]
}

/** Endpoint a "kept 2 of 3, dismissed 1" refinement is POSTed to. */
const REFINE_ENDPOINT = "/tenders/refine"

export type RefineResult = {
  removed: Record<string, unknown>
  new_tolerance: Record<string, number>
  replacement: TenderMatch | null
}

/**
 * The user was shown exactly 3 tenders (one per reel column) and dismissed
 * one of them. Sends all 3 (by their full raw markdown, from
 * TenderMatch.tender.markdown) plus which index was dismissed; the backend
 * nudges filters.yaml's per-criterion tolerance toward the 2 kept and away
 * from the dismissed one, re-runs the fetch, and returns ONE replacement
 * tender for that slot (see backend/main.py's /tenders/refine and
 * workflow_tools/8_change_filter_tolerance.py).
 */
export async function refineTendersRequest(
  tenders: [string, string, string],
  removedIndex: 0 | 1 | 2,
  onProgress?: (event: MatchProgressEvent) => void,
  signal?: AbortSignal,
): Promise<RefineResult> {
  const event = await streamPipelineRequest(
    REFINE_ENDPOINT,
    { tenders, removed_index: removedIndex },
    onProgress,
    signal,
    "the tender refine service",
  )
  const { type: _type, ...rest } = event
  return rest as RefineResult
}