# Security Best Practices Report

## Executive summary
The repository has a solid direction on secret externalization and same-origin frontend routing, but it still contains a critical authentication design flaw and multiple high-risk production hardening gaps. The most important issues are the current cookie session format, placeholder local credentials that still fail open, and unauthenticated state-changing backend endpoints that mutate shared runtime state.

## Review scope
- Backend:
  - `backend/web/app.py`
  - `backend/core/auth_local.py`
  - `backend/core/config_loader.py`
  - `backend/config.yaml`
  - `backend/storage/database.py`
  - `backend/storage/repository.py`
  - `backend/workers/coletor.py`
- Frontend:
  - `frontend/src/`
  - `frontend/index.html`
- Deployment and CI:
  - `vercel.json`
  - `.github/workflows/monitor_dinamico.yml`
- Excluded from this review:
  - `backend/tests/`
  - `backend/docs/`
  - temporary helper scripts such as `backend/tmp_test_supa.py` and `backend/test_supa_key.py`

## Critical findings

### SBP-001
- Rule ID: FASTAPI-SESS-002 / FASTAPI-AUTH-001
- Severity: Critical
- Location:
  - `backend/core/auth_local.py:30-44`
  - `backend/core/auth_local.py:55-77`
- Evidence:
  - `secret = auth_config.get("session_secret", "trocar-em-dev")`
  - `session_token = f"{username}|{secret}"`
  - `username, token_secret = token.split("|")`
  - `if token_secret != secret:`
- Impact:
  - The session cookie contains the server-side `session_secret` in clear text, so any user who receives a valid cookie can recover that secret and forge a cookie for any username.
  - This collapses the only current auth boundary for `/painel` and `/rotas/*`.
- Fix:
  - Replace the cookie value with an opaque random session identifier stored server-side, or a properly signed token that does not reveal the signing secret.
  - Fail startup if placeholder auth secrets are still present outside an explicit dev mode.
- Mitigation:
  - Rotate the current `AUTH_LOCAL_SESSION_SECRET` immediately after changing the implementation.
  - In the interim, reduce exposure by restricting auth-protected routes at the edge to a trusted audience.
- False positive notes:
  - This is a direct code-level issue, not an infrastructure-dependent inference.

## High findings

### SBP-002
- Rule ID: FASTAPI-AUTH-001 / FASTAPI-AUTH-003
- Severity: High
- Location:
  - `backend/config.yaml:19-24`
  - `backend/core/config_loader.py:75-101`
  - `backend/core/auth_local.py:18-24`
- Evidence:
  - `auth_local.enabled: true`
  - `username: "operacao"`
  - `password: "definir_localmente"`
  - `session_secret: "trocar-em-producao"`
  - `get_credentials()` falls back to those same placeholder values if environment overrides are absent.
- Impact:
  - A production deployment that misses environment overrides will still boot with authentication enabled and predictable credentials.
  - Combined with SBP-001, a single login with placeholder credentials becomes a full operator-session forgery path.
- Fix:
  - Change the production default posture to fail closed:
    - set `auth_local.enabled` to `false` in versioned config, or
    - refuse startup when placeholder username, password, or secret are detected.
  - Require environment-backed secrets for any non-dev deployment.
- Mitigation:
  - Add a startup log at `error` level when placeholder auth values are detected, and abort before binding the HTTP listener.
- False positive notes:
  - This risk is realized only if the backend is deployed without real environment overrides, but the code currently allows exactly that.

### SBP-003
- Rule ID: FASTAPI-AUTHZ-001
- Severity: High
- Location:
  - `backend/web/app.py:447-483`
  - `backend/web/app.py:497-503`
  - `backend/web/app.py:137-148`
- Evidence:
  - `@app.post("/favoritos", status_code=201)` has no `Depends(verificar_autenticacao)`.
  - `@app.delete("/favoritos")` has no `Depends(verificar_autenticacao)`.
  - `@app.delete("/cache")` has no `Depends(verificar_autenticacao)`.
  - Those handlers write shared state through `_salvar_favoritos()` and `cache.clear()`.
- Impact:
  - Any unauthenticated caller can mutate shared route configuration or flush the in-memory cache.
  - This allows integrity tampering for all users and makes quota/latency abuse easier by forcing cache misses.
- Fix:
  - Add authentication dependencies to all shared-state mutation endpoints.
  - If browser cookie auth remains the mechanism, add CSRF protection for any authenticated state-changing routes.
  - Move mutable operator data away from a shared flat file when possible.
- Mitigation:
  - At minimum, restrict these paths at the reverse proxy until route-level auth is added.
- False positive notes:
  - If these routes are intentionally public, this is still a security design choice that should be documented because they alter shared server-side state.

### SBP-004
- Rule ID: FASTAPI-SSRF-001 (cost/egress surface) / FASTAPI-DEPLOY-001
- Severity: High
- Location:
  - `backend/web/app.py:257-277`
  - `backend/web/app.py:383-436`
  - `backend/web/app.py:617-634`
  - `frontend/src/app/services/api.ts:1-22`
- Evidence:
  - Public endpoints `/consultar`, `/exportar/excel`, `/exportar/csv`, and their aliases trigger the server-side consult pipeline with user-controlled route inputs.
  - No in-repo rate limiting, auth gate, or request budgeting is visible on those endpoints.
- Impact:
  - An unauthenticated attacker can repeatedly trigger paid upstream lookups, burning Google/HERE quota and degrading availability.
  - This is not classic arbitrary-destination SSRF, but it is still a high-value outbound abuse surface.
- Fix:
  - Require authentication for expensive consult/export endpoints unless there is a hard business reason not to.
  - Add per-IP and per-user rate limiting at the edge and/or in app middleware.
  - Cache repeated free-form lookups safely where business rules allow.
- Mitigation:
  - Add provider quota alerts and fast-fail logic when upstream error rates spike.
- False positive notes:
  - If strong rate limits already exist outside the repo, the severity drops, but no such control is visible here.

## Medium findings

### SBP-005
- Rule ID: FASTAPI-OPENAPI-001 / REACT-HEADERS-001
- Severity: Medium
- Location:
  - `backend/web/app.py:49-53`
  - `vercel.json:1-28`
- Evidence:
  - The FastAPI app is created with default docs settings; no `docs_url=None`, `redoc_url=None`, or `openapi_url=None` is configured.
  - `vercel.json` defines rewrites only; there is no `headers` block for CSP, `X-Frame-Options` or `frame-ancestors`, `X-Content-Type-Options`, or `Referrer-Policy`.
- Impact:
  - Public docs and OpenAPI metadata increase route discoverability for attackers.
  - Missing in-repo browser hardening means the production posture depends on undocumented external configuration.
- Fix:
  - Disable or gate FastAPI docs in production.
  - Add explicit edge headers in `vercel.json` or document where they are enforced outside the repo.
  - Consider `TrustedHostMiddleware` or equivalent host validation if the backend is directly internet-facing.
- Mitigation:
  - Add synthetic checks that verify headers at runtime even if they are managed outside the repository.
- False positive notes:
  - Security headers may already be injected by Vercel, Render, or another upstream layer; that is not visible in repo code.

## Low findings

### SBP-006
- Rule ID: REACT-HEADERS-001 / REACT-AUTHZ-001 (information disclosure)
- Severity: Low
- Location:
  - `frontend/src/app/App.tsx:15-31`
- Evidence:
  - The error boundary renders both `err.message` and `err.stack` directly to end users.
- Impact:
  - Production users can see internal component stack traces and error messages that help with route and component reconnaissance.
- Fix:
  - Replace the raw stack rendering with a generic production-safe error message.
  - Optionally gate detailed traces behind a dev-only build flag.
- Mitigation:
  - Capture detailed traces in a server-side or observability tool instead of exposing them in the browser.
- False positive notes:
  - If this build is strictly internal-only, the impact is lower, but it is still avoidable leakage.

## Positive controls observed
- `backend/core/config_loader.py:41-103` centralizes environment overrides instead of hard-coding live secrets into runtime code.
- `backend/core/auth_local.py:38-44` sets `HttpOnly` and `SameSite=Lax`, and `Secure` is configurable by environment.
- `frontend/src/app/services/api.ts:1-22` uses same-origin relative URLs instead of embedding a public API base URL in the client.
- `frontend/src/app/pages/ConsultaPage.tsx:509-530` uses `rel="noopener noreferrer"` for external map links.
- `vercel.json:3-4` uses `npm ci`, which is the correct reproducible install path for the frontend build.

## Recommended remediation order
1. Fix SBP-001 immediately and rotate the auth session secret.
2. Make auth fail closed in production by addressing SBP-002.
3. Protect or remove anonymous state-changing endpoints from SBP-003.
4. Add rate limiting and auth boundaries for expensive endpoints from SBP-004.
5. Capture explicit production hardening in repo config for SBP-005.

## Report metadata
- Guidance sources used:
  - `security-best-practices/references/python-fastapi-web-server-security.md`
  - `security-best-practices/references/javascript-typescript-react-web-frontend-security.md`
  - `security-best-practices/references/javascript-general-web-frontend-security.md`
- Report output path:
  - `security_best_practices_report.md`
