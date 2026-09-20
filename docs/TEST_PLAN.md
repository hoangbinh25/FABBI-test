# Manual Test Plan

## Scope

Manual regression coverage for authentication, authorization, todo CRUD, and cache isolation.

## Environment

| Item | Value |
| --- | --- |
| Frontend | `http://localhost:3000` |
| API / Swagger | `http://localhost:8000` / `http://localhost:8000/docs` |
| Services | `docker compose up --build` from repository root |
| Accounts | Create User A and User B with separate browser sessions |

Use a normal browser session for User A and an incognito session for User B.

## Authentication

### AUTH-01 — Register a new account

- **Priority / Severity:** P0 / Critical
- **Preconditions:** App is running; email has not been registered.
- **Steps:** Open `/register`, enter valid credentials, then submit.
- **Expected:** API returns `201`; browser opens the todo page and displays the account email.
- **Actual / Status:** Not run.

### AUTH-02 — Reject an invalid password

- **Priority / Severity:** P0 / High
- **Preconditions:** A registered account exists.
- **Steps:** Open `/login`, enter that email and an invalid password, then submit.
- **Expected:** Login remains unavailable; an authentication error appears and no tokens are stored.
- **Actual / Status:** Not run.

### AUTH-03 — Logout clears the browser session

- **Priority / Severity:** P0 / High
- **Preconditions:** User A is logged in and has a visible todo.
- **Steps:** Click **Logout**; inspect local storage; navigate to `/`.
- **Expected:** Both tokens are removed and protected routes do not render User A data.
- **Actual / Status:** Not run.

### AUTH-04 — Invalid or expired token clears the session

- **Priority / Severity:** P1 / High
- **Preconditions:** User A is logged in.
- **Steps:** Replace `access_token` with invalid text in DevTools, then refresh.
- **Expected:** Browser redirects to `/login`; both tokens and cached user data are cleared.
- **Actual / Status:** Not run.

## Authorization

### AUTHZ-01 — User B cannot read User A's todo

- **Priority / Severity:** P0 / Critical
- **Preconditions:** User A created todo X; User B is logged in separately.
- **Steps:** In Swagger, authorize as B and call `GET /api/v1/todos/{X}`.
- **Expected:** `404`; title and description of X are not exposed.
- **Actual / Status:** Not run.

### AUTHZ-02 — User B cannot update User A's todo

- **Priority / Severity:** P0 / Critical
- **Preconditions:** Same as AUTHZ-01.
- **Steps:** As B, call `PUT /api/v1/todos/{X}` with a new title; reload as A.
- **Expected:** B receives `404`; A's todo is unchanged.
- **Actual / Status:** Not run.

### AUTHZ-03 — User B cannot delete User A's todo

- **Priority / Severity:** P0 / Critical
- **Preconditions:** Same as AUTHZ-01.
- **Steps:** As B, call `DELETE /api/v1/todos/{X}`; reload A's list.
- **Expected:** B receives `404`; X remains in A's list.
- **Actual / Status:** Not run.

## Todo behavior

### TODO-01 — Create, edit, and delete a todo

- **Priority / Severity:** P0 / High
- **Preconditions:** User A is logged in.
- **Steps:** Create with title and description; edit its title; delete it; refresh after each operation.
- **Expected:** Each change persists; deleted todo does not return.
- **Actual / Status:** Not run.

### TODO-02 — Toggle completed both directions

- **Priority / Severity:** P1 / Medium
- **Preconditions:** User A has an active todo.
- **Steps:** Mark it completed; refresh; mark it active again; refresh.
- **Expected:** The `completed` value persists as `true`, then as `false`.
- **Actual / Status:** Not run.

### TODO-03 — Partial update preserves description

- **Priority / Severity:** P1 / Medium
- **Preconditions:** User A has a todo with a non-empty description.
- **Steps:** Edit only the title and save; refresh.
- **Expected:** New title is saved and description is unchanged.
- **Actual / Status:** Not run.

## Cache regression

### CACHE-01 — Todo lists are isolated by user

- **Priority / Severity:** P0 / Critical
- **Preconditions:** A and B have different todos.
- **Steps:** Load A's list twice; load B's list in a second session; repeat in reverse order.
- **Expected:** Each account sees only its own todos.
- **Actual / Status:** Not run.

### CACHE-02 — Create invalidates cached lists

- **Priority / Severity:** P1 / High
- **Preconditions:** User A loaded an empty list.
- **Steps:** Create a todo, then reload.
- **Expected:** New todo appears immediately and after reload.
- **Actual / Status:** Not run.

### CACHE-03 — Update and delete invalidate cached lists

- **Priority / Severity:** P1 / High
- **Preconditions:** User A has loaded a list containing a todo.
- **Steps:** Update title and reload; delete todo and reload.
- **Expected:** Updated title persists; deleted todo does not reappear.
- **Actual / Status:** Not run.

### CACHE-04 — Switching accounts clears React Query data

- **Priority / Severity:** P0 / High
- **Preconditions:** A has a visible todo; B has none.
- **Steps:** Login as A, logout, then login as B in the same tab.
- **Expected:** A's email and todos never appear during B's session, including loading state.
- **Actual / Status:** Not run.

## Defect report template

- Test case ID and execution time.
- Account and todo UUID; never include passwords or token values.
- Actual HTTP status/body with tokens redacted.
- Screenshot, console output, and relevant Network request.
- Confirmed priority, severity, and reproduction steps.
