# Todo Sharing — Technical Specification

## 1. Objective

Allow a user (the **owner**) to share their complete todo collection with another existing user (the **collaborator**). A collaborator has either **viewer** access, which permits reading, or **editor** access, which permits reading and editing todos in that owner's collection. The owner can change a collaborator's permission or revoke access at any time.

The current product has no `todo_lists` entity: a user's collection is represented by all `todos` where `todos.user_id = owner_user_id`. A share therefore applies to the owner's current and future todos.

## 2. Roles and permission matrix

| Operation | Owner | Viewer | Editor | Unrelated user |
| --- | --- | --- | --- | --- |
| Read owner collection | Yes | Yes | Yes | No |
| Create todo in owner collection | Yes | No | Yes | No |
| Update/delete todo in owner collection | Yes | No | Yes | No |
| List/manage collaborators | Yes | No | No | No |
| Change/revoke a share | Yes | No | No | No |
| Re-share collection | Out of scope | No | No | No |

The todo's `user_id` remains the owner ID even when an editor creates or changes it. The API response includes an `owner_id` and `access_role` for shared items so clients can show the collection context.

## 3. User stories and acceptance criteria

### US-1: Share a collection

**As an owner, I want to share my todo collection with an existing user as a viewer or editor so that we can collaborate at the appropriate permission level.**

Acceptance criteria:

- Owner can submit a registered user's email and either `viewer` or `editor`.
- A successful grant returns `201 Created`, the share ID, recipient, permission, and timestamps.
- Recipient can immediately read the owner's existing and future todos according to the granted role.
- Owner cannot share with their own account; API returns `422`.
- Unknown recipient returns `404` without revealing any additional account information.
- An active share for the same owner/recipient cannot be duplicated; API returns `409`.

### US-2: Consume a shared collection

**As a viewer or editor, I want to see collections shared with me so that I can work from one authenticated account.**

Acceptance criteria:

- `GET /todos` returns items owned by the current user plus items from active incoming shares; each item identifies its owner and access role.
- Viewer can read shared todos but receives `403` for create, update, or delete attempts in that collection.
- Editor can create, update, and delete in the shared collection while their `editor` share remains active.
- An unrelated user receives `404` for a direct todo ID lookup, preserving the current no-resource-enumeration behavior.

### US-3: Change permission or revoke access

**As an owner, I want to downgrade, upgrade, or revoke a collaborator's access so that permissions remain current.**

Acceptance criteria:

- Owner can change `viewer` to `editor` and `editor` to `viewer`; response returns the new version and timestamp.
- Owner can delete the share; subsequent collaborator reads receive no shared items and writes receive `404` or `403` according to endpoint semantics.
- Revoke is effective for a request that begins after the revoke transaction commits.
- Changing/revoking a share immediately invalidates all cached todo-list variants for the owner and collaborator.
- Only the owner can modify/delete the share; collaborator and unrelated users receive `404`.

## 4. Scope

### In scope

- Direct sharing with an existing registered user by email.
- `viewer` and `editor` permissions.
- List owned/incoming shares, change permission, revoke access.
- Shared todo reads and editor writes.
- Permission-aware cache invalidation and audit-friendly timestamps.

### Out of scope

- Email, push, or in-app invitation notifications and acceptance workflow.
- Public links, anonymous access, expiration dates, groups, teams, or nested roles.
- Re-sharing by collaborators, ownership transfer, collaborative comments, activity feed, and audit-log UI.
- Sharing individual todos independently of the owner collection.
- Conflict-resolution UI beyond optimistic concurrency responses.

## 5. Data model

### `todo_collection_shares`

| Field | Type | Rules |
| --- | --- | --- |
| `id` | UUID | Primary key; generated server-side. |
| `owner_user_id` | UUID | Required FK to `users.id`; identifies the collection owner. |
| `collaborator_user_id` | UUID | Required FK to `users.id`; recipient of access. |
| `permission` | VARCHAR(10) | Required; database check permits only `viewer` or `editor`. |
| `version` | INTEGER | Required, default `1`; incremented on permission changes for optimistic concurrency. |
| `created_at` | TIMESTAMPTZ | Required, default current UTC timestamp. |
| `updated_at` | TIMESTAMPTZ | Required, default current UTC timestamp. |

Constraints and indexes:

```sql
PRIMARY KEY (id);
UNIQUE (owner_user_id, collaborator_user_id);
CHECK (owner_user_id <> collaborator_user_id);
CHECK (permission IN ('viewer', 'editor'));
FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE;
FOREIGN KEY (collaborator_user_id) REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX ix_todo_collection_shares_collaborator
  ON todo_collection_shares (collaborator_user_id, owner_user_id);
```

Deleting an owner or collaborator deletes the related share records. Deleting a todo does not affect collection shares. No `todos` schema change is required because `todos.user_id` already identifies the collection owner.

## 6. API contracts

All endpoints require a valid access token. Error responses use:

```json
{
  "detail": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE"
}
```

| Method | Endpoint | Purpose | Success | Principal |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/todo-shares` | Create a share | `201` | Owner |
| `GET` | `/api/v1/todo-shares` | List shares owned by caller | `200` | Owner |
| `GET` | `/api/v1/todo-shares/received` | List collections shared with caller | `200` | Collaborator |
| `PATCH` | `/api/v1/todo-shares/{share_id}` | Change permission | `200` | Owner |
| `DELETE` | `/api/v1/todo-shares/{share_id}` | Revoke access | `204` | Owner |
| `GET` | `/api/v1/todos` | List owned plus shared todos | `200` | Owner/viewer/editor |
| `POST` | `/api/v1/todos` | Create owned/shared todo | `201` | Owner/editor |
| `GET/PATCH/DELETE` | `/api/v1/todos/{todo_id}` | Read or mutate according to role | `200/204` | Owner/viewer/editor |

### Create share

```json
POST /api/v1/todo-shares
{
  "collaborator_email": "teammate@example.com",
  "permission": "editor"
}
```

- `201`: share object.
- `404 USER_NOT_FOUND`: email is not registered.
- `409 SHARE_ALREADY_EXISTS`: owner/recipient pair already exists.
- `422 SELF_SHARE_NOT_ALLOWED` or invalid permission.

### Update share permission

```json
PATCH /api/v1/todo-shares/7df7b5e0-0b79-4b59-b985-f15571ed32b1
{
  "permission": "viewer",
  "version": 3
}
```

- `200`: updated share with incremented version.
- `409 SHARE_VERSION_CONFLICT`: another owner action changed/revoked the share; client must reload.
- `404 SHARE_NOT_FOUND`: no share exists or caller is not its owner.
- `422`: invalid permission or version.

### Create a todo in a shared collection

```json
POST /api/v1/todos
{
  "title": "Prepare release notes",
  "description": "Draft by Friday",
  "collection_owner_id": "b5c3b8d4-7d87-4a09-9386-2a4c6356d8e0"
}
```

`collection_owner_id` is optional; omitted means caller's own collection. It must equal the caller or identify an active `editor` share. Viewer receives `403 READ_ONLY_SHARE`.

### Todo response additions

```json
{
  "id": "...",
  "title": "Prepare release notes",
  "user_id": "b5c3...",
  "owner_id": "b5c3...",
  "access_role": "editor"
}
```

## 7. Authorization, concurrency, and edge cases

- Authorize every todo request against either `todo.user_id == current_user.id` or an active share for `(todo.user_id, current_user.id)`; never trust `collection_owner_id` without this lookup.
- Return `404` for direct todo/share resources that are inaccessible to avoid resource enumeration. Use `403` when a known, already-authorized shared collection operation is forbidden by the `viewer` role.
- Validate self-share before querying/mutating; database check is the final safety net.
- Create uses the unique constraint as the race-safe duplicate guard. If two requests race, map integrity error to `409 SHARE_ALREADY_EXISTS`.
- Permission update/revoke uses `WHERE id = :id AND owner_user_id = :owner AND version = :version`; zero affected rows becomes `409` if the share still exists or `404` if it does not.
- A todo write transaction re-checks active editor access before committing. A revoke committed first prevents a later write; a write committed first remains a historical change and revoke applies thereafter.
- Owner deleting their user cascades shares and todos through existing ownership policy; collaborator deletion only cascades their share rows.

## 8. Cache strategy

List cache keys must include the requesting viewer and all query parameters, for example:

```text
todos:list:{requesting_user_id}:{cache_version}:{page}:{size}:{filters_hash}
```

Do not cache only by owner ID: an owner's and collaborator's visible result sets differ. Rotate/invalidate the cache version for all affected users after a committed transaction:

- grant, permission change, or revoke: owner and collaborator;
- owner/editor creates, updates, or deletes a shared todo: owner and every active collaborator for that owner;
- account deletion: affected owner/collaborator cache namespaces.

Cache invalidation runs after database commit. Cache failure must be observable and recoverable; it must not silently grant authorization.

## 9. Observability and rollout

- Log share create/change/revoke events with actor ID, owner ID, collaborator ID, share ID, and outcome; exclude tokens and todo content.
- Add migration, API authorization tests, and cache-invalidation tests before enabling routes.
- Release read support and owner management behind a feature flag; enable editor writes after authorization metrics are stable.
