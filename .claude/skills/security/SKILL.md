---
name: security
description: Security checklist for writing or reviewing code. Use when a change touches authentication, authorization/permissions, user input handling, file uploads, payments, cryptography, personal data, secrets/config, CORS/CSP, or when asked for a security review.
---
# Security checklist

Apply what's relevant to the change. Anything you can't satisfy → tell the developer.

## Secrets & config
- No secrets in code, tests, fixtures, logs, error messages or docs. Env vars only.
- New env var → add to `.env.example` (dummy value, one-line comment) in the same commit.
- A secret that reached git history is compromised → stop, report, rotation is the fix.

## Input & injection
- Validate at the server boundary: type, length, format, allowed values.
- SQL: ORM or parameterized queries only — never string-built.
- No `eval`/`exec`, no shell commands built from input (no `shell=True` with input).
- File paths from input: normalize and confine to an allowed directory (traversal).
- Deserialization: never unpickle/unsafe-load untrusted data.
- Outbound requests to user-supplied URLs: allowlist (SSRF).

## AuthN / AuthZ
- Every endpoint enforces authentication and authorization **server-side**.
- Ownership checks on every object access — an ID in the URL is not permission (IDOR).
- Use the framework's password hashing, sessions and CSRF protection. No custom crypto.
- Rate-limit auth endpoints and anything expensive.

## Output & transport
- Escape output by default; never render raw user content as HTML.
- No wildcard CORS with credentials. Keep CSP tight; new third-party origins are a
  deliberate, reviewed change.
- Cookies: `HttpOnly`, `Secure`, `SameSite`.

## Errors & logging
- Users get generic messages; stack traces, SQL and paths go to logs only.
- Logs never contain passwords, tokens, full card numbers or unnecessary personal data.

## Uploads
- Check size and type server-side (content, not just extension); store outside the web
  root or in object storage; never execute or serve with a guessed content type.

## Dependencies
- See the `new-dependency` skill. Run the audit command from Project facts when
  dependencies change.

## Reporting
For each finding: location, impact, suggested fix. Never exploit, never test against
staging/production, never fix silently as a side effect.
