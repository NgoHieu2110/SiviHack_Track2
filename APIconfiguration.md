# SYSTEM SPECIFICATION: API CONTRACT & DATA STRUCTURES

## 1. GLOBAL CONFIGURATION & CONVENTIONS
- **Architecture**: RESTful APIs
- **Authentication**: JWT via `Authorization: Bearer <access_token>`
- **Content-Type**: `application/json`
- **Date Standard**: ISO 8601 UTC (`YYYY-MM-DDTHH:mm:ssZ`)

---

## 2. STANDARD ERROR RESPONSE
All non-2xx HTTP responses MUST strictly follow this JSON payload shape:

```json
{
  "success": false,
  "error": {
    "code": "STRING_ERROR_CODE",
    "message": "Human readable error message",
    "details": []
  }
}