## Plan: Agentic AI Integration

TL;DR - Implement an agentic AI inside `app/ai/` that uses the Mistral model `mistral-large-latest` to perform function-calling tasks (DB reads/writes, reports, emails). The agent will enforce role-based permissions using the existing Flask `session` flags (admin, principal, teacher). Provide a client wrapper, an AI context class capturing the current user session, function handlers that validate permissions and perform DB operations via existing SQLAlchemy models, and an agent orchestration layer that exposes a safe function-calling surface.

**Steps**
1. Scaffold AI package and client
   - Add `app/ai/__init__.py`, `app/ai/client.py`, `app/ai/agent.py`, `app/ai/context.py`, `app/ai/functions.py`.
   - `client.py`: wrapper for Mistral API configured from `app/config.py`.
   - `agent.py`: high-level orchestration (receive prompt, call model, dispatch function calls, return structured text).
   - *depends on step 2* for config and requirements.

2. Configuration & dependencies
   - Add `MISTRAL_API_KEY` (or `MISTRAL_API_TOKEN`) to [app/config.py](app/config.py).
   - Add necessary SDK to `requirements.txt` (official Mistral SDK or `mistral-client`/`requests` wrapper). Document env var usage.

3. AI Context & permission model
   - Implement `AIContext` class in `app/ai/context.py` that encapsulates `session` info, current user id, role flags, and a `has_permission(permission_name)` helper.
   - Use existing session flags (`session.get("admin")`, `session.get("teacher")`, etc.) to determine permissions.

4. Function handlers (function-calling surface)
   - Implement `app/ai/functions.py` defining explicit functions the agent can call, e.g.:
     - `get_teacher_details(teacher_id)` — read-only, allowed for admin/principal/teacher(if own id).
     - `add_teacher(payload)` — create, allowed only for `admin` or `principal`.
     - `get_students_by_teacher(teacher_id)` — read-only.
     - `fetch_attendance(teacher_id, date_range)` — read-only.
     - `generate_report(query_params)` — composes PDF/HTML using existing PDF libs.
     - `send_email(recipient, subject, body)` — requires an allow-list and additional permission.
   - Each function must accept an `AIContext` instance and immediately validate permissions; on failure, return a structured error object with HTTP-like code and message.
   - Functions should use existing SQLAlchemy models (e.g. models in [app/models/](app/models/)) and `db.session` from [app/extensions.py](app/extensions.py).

5. Agent orchestration & safety
   - Agent receives user prompt plus `AIContext` (server-side). The agent calls the model and uses function-calling (Mistral's tool/call API) to request functions.
   - Implement a function-dispatcher that verifies function name & params are allowed and maps them to `app/ai/functions.py` functions.
   - Log each agent action to an `AgentAudit` model/table (who requested, timestamp, function called, args, model response) to facilitate auditing.

6. Integration with Flask app
   - Expose a small secure endpoint or internal interface to invoke the agent (e.g., register an `ai` blueprint), or provide a service object for server-side invocation in existing routes.
   - Wire initialization in [app/__init__.py](app/__init__.py) similar to other extensions.

7. Tests & verification
   - Unit tests for `AIContext.has_permission()` with combinations of session flags.
   - Unit tests for function handlers verifying permission rejection and DB operations.
   - Integration test exercising a sample prompt that triggers a permitted function call and an attempted unauthorized action.

8. Deployment & ops
   - Document required env vars (`MISTRAL_API_KEY`), how to add to the instance or container, and any rate-limit considerations.
   - Recommend adding background worker (`rq`/`celery`) if agent tasks like report generation or email sending are long-lived.

**Relevant files**
- [app/config.py](app/config.py) — add `MISTRAL_API_KEY` / config entries.
- [requirements.txt](requirements.txt) — add Mistral SDK / HTTP client and mail/report libs.
- [app/extensions.py](app/extensions.py) — optionally register `ai_client` or keep client local to `app/ai`.
- [app/__init__.py](app/__init__.py) — initialize/register AI blueprint/service.
- [app/ai/__init__.py](app/ai/__init__.py) — new package entry.
- [app/ai/client.py](app/ai/client.py) — Mistral API wrapper.
- [app/ai/context.py](app/ai/context.py) — `AIContext` class wrapping Flask `session`.
- [app/ai/functions.py](app/ai/functions.py) — secured function implementations calling SQLAlchemy models.
- [app/ai/agent.py](app/ai/agent.py) — orchestrator implementing function-calling flow.
- [app/models/agent.py](app/models/agent.py) — `AgentAudit` model for logging (new file).
- [app/routes/auth/login.py](app/routes/auth/login.py) — reference for session flag shapes.
- [app/extensions.py](app/extensions.py) — `db` usage reference.

**Verification**
1. Unit tests: `tests/test_ai_context.py`, `tests/test_functions_permissions.py` to assert allowed/denied flows.
2. Integration test: simulate a request with a session for `principal` that calls `add_teacher` and confirm DB row created and `AgentAudit` row logged.
3. Manual test: set `MISTRAL_API_KEY` locally and run a prompt that requests a function call; observe function dispatch and model replies.

**Decisions / Assumptions**
- Use Mistral model `mistral-large-latest` via its SDK or HTTP API as primary LLM.
- Keep role checks simple by reusing existing `session` flags rather than introducing Flask-Login immediately.
- All agent-invoked DB writes must be explicit functions (no direct arbitrary SQL execution).
- Agent runs server-side; it is never given direct DB credentials or full app privileges — every function receives `AIContext` and enforces checks.

**Further Considerations / Questions**
1. Do you want the agent exposed as a REST endpoint (e.g., `/ai/agent`) or only used internally by server-side workflows?
2. Preferred background worker for long tasks? Options: `rq` (simple), `celery` (full-featured), or none (sync with warnings).
3. Should we harden authentication first (password hashing, optional Flask-Login) before enabling write functions for safety?


