# Manual Test Plan — Authentication, Authorization, Todo and Cache Regression

## 1. Scope and objective

This plan covers authentication, authorization boundaries, todo CRUD, browser-session cleanup, and cache correctness for the Tier 1 and Tier 2 changes. It is intended for manual execution against the Docker Compose environment.

## 2. Environment and prerequisites

| Item | Value |
| --- | --- |
| Frontend | `http://localhost:3000` |
| Backend API / Swagger | `http://localhost:8000` / `http://localhost:8000/docs` |
| Browser | Latest Chrome or Chromium, with DevTools available |
| Services | Run `docker compose up --build` from the repository root |
| Accounts | Create two unique accounts during testing: User A and User B |
| Seed data | Not required; each case creates its own todo data |

Use a normal browser window for User A and an incognito window (or separate browser profile) for User B when the case requires concurrent sessions.

## 3. Test cases

| ID | Module | Scenario | Preconditions | Steps | Expected result | Actual result | Priority | Severity | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AUTH-01 | Authentication | Register a new account | App is running; email has not been registered | 1. Open `/register`.<br>2. Enter valid email, password, and matching confirmation.<br>3. Click **Create Account**. | API returns 201; browser moves to Todo page; displayed email matches the new account. | Not run | P0 | Critical | Not run |
| AUTH-02 | Authentication | Reject an invalid password | A registered account exists | 1. Open `/login`.<br>2. Enter the account email with an incorrect password.<br>3. Click **Sign In**. | Login remains on the page; user sees an authentication error; no access or refresh tokens are stored. | Not run | P0 | High | Not run |
| AUTH-03 | Authentication | Logout clears the browser session | User A is logged in and has at least one todo visible | 1. Click **Logout**.<br>2. Verify redirect to `/login`.<br>3. In DevTools Application/Storage, inspect local storage.<br>4. Navigate to `/`. | User is on login page; `access_token` and `refresh_token` are absent; protected route does not render A's todos. | Not run | P0 | High | Not run |
| AUTH-04 | Authentication | A 401 clears the browser session | User A is logged in | 1. In DevTools, replace `access_token` with invalid text.<br>2. Refresh or trigger a protected request.<br>3. Inspect local storage. | Browser redirects to `/login`; both tokens are removed; prior profile/todo data does not remain visible. | Not run | P1 | High | Not run |
| AUTHZ-01 | Authorization | User B cannot read A's todo by ID | A and B exist; A created todo X | 1. Obtain X's UUID from DevTools Network or Swagger.<br>2. Log in as B.<br>3. In Swagger authorize with B's token and call `GET /api/v1/todos/{X}`. | HTTP 404; response does not expose X's title or description. | Not run | P0 | Critical | Not run |
| AUTHZ-02 | Authorization | User B cannot update A's todo | Same as AUTHZ-01 | 1. As B call `PUT /api/v1/todos/{X}` with a different title.<br>2. As A reload the todo. | B receives HTTP 404; A's title and all fields are unchanged. | Not run | P0 | Critical | Not run |
| AUTHZ-03 | Authorization | User B cannot delete A's todo | Same as AUTHZ-01 | 1. As B call `DELETE /api/v1/todos/{X}`.<br>2. As A reload the todo list. | B receives HTTP 404; X remains in A's list. | Not run | P0 | Critical | Not run |
| TODO-01 | Todo CRUD | Create, edit, then delete a todo | User A is logged in | 1. Create a todo with title and description.<br>2. Confirm it appears.<br>3. Edit title.<br>4. Delete it.<br>5. Refresh after every operation. | Each confirmed change persists after refresh; deleted item does not return. | Not run | P0 | High | Not run |
| TODO-02 | Todo status | Mark a todo complete | User A has an active todo | 1. Click the todo checkbox.<br>2. Confirm strike-through/completed UI.<br>3. Refresh. | Todo remains completed after refresh. | Not run | P1 | Medium | Not run |
| TODO-03 | Todo status regression | Mark a completed todo active | User A has a completed todo | 1. Click the completed todo checkbox again.<br>2. Refresh. | Expected: todo remains active (`completed=false`) after refresh.<br>Known current limitation: source has not yet fixed this behavior; record observed result as a defect if it reverts. | Not run | P1 | Medium | Not run |
| TODO-04 | Partial update regression | Change title without losing description | User A has a todo with a non-empty description | 1. Open edit.<br>2. Change title only and save.<br>3. Refresh. | Expected: description is retained.<br>Known current limitation: source has not yet fixed this behavior; record observed result as a defect if description clears. | Not run | P1 | Medium | Not run |
| CACHE-01 | Backend cache | A and B list data remains isolated | A and B have distinct todos | 1. As A load list and refresh once.<br>2. As B log in in separate session and load list.<br>3. Repeat in reverse order. | Each user sees only their own todos; no title from the other user appears. | Not run | P0 | Critical | Not run |
| CACHE-02 | Backend cache | Create invalidates cached list | User A is logged in; load list once | 1. Create a new todo.<br>2. Reload the page. | New todo appears immediately and after reload. | Not run | P1 | High | Not run |
| CACHE-03 | Backend cache | Update/delete invalidates cached list | User A has a todo and has loaded the list | 1. Update its title, reload.<br>2. Delete it, reload. | Updated title persists; deleted item does not reappear. | Not run | P1 | High | Not run |
| CACHE-04 | Frontend cache | Switching accounts clears React Query data | A has a visible todo; B has none | 1. Log in as A and wait for list.<br>2. Logout.<br>3. Log in as B in the same tab. | A's email and todo never appear in B's session, including while B's request is loading. | Not run | P0 | High | Not run |

## 4. Defect reporting format

For a failed manual case, record:

- Test case ID and execution date/time.
- Account and todo UUID used, without recording passwords or token values.
- Actual response status/body (redact access and refresh tokens).
- Screenshot, browser console output, and relevant Network request.
- Severity/priority confirmed by the test owner and reproduction steps.

## 5. Known limitations at the time of writing

- JWT expiration validation is outside the current Tier 1 patch; a manually created expired token should be treated as a known defect until fixed.
- `completed: true` to `false` and preserving description during title-only updates are tracked by TODO-03 and TODO-04 as known source limitations.
- The current UI has no pagination controls. Pagination/cache parameters can be verified through Swagger or browser Network requests.
