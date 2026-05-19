# Notification UI Implementation Notes

Branch: `notification-ui`

This branch adds an authenticated notification system to the quiz app. The work covers backend notification storage and APIs, frontend API helpers, a navbar notification bell, a user inbox page, and an admin notification page for direct and broadcast messages.

The implementation intentionally does not add login-flow notification creation. Login-generated security notifications can be added later, but the current scope is focused on admin/system notifications that users can read, mark as read, and delete.

## Why This Was Implemented

The app needed a way to send account, system, admin, payment, or security messages to signed-in users without relying on email or one-off UI banners.

The notification system was added so that:

- Authenticated users can see unread notifications from the navbar.
- Users have a persistent inbox at `/notifications`.
- Admins can create direct notifications for a specific user.
- Admins can broadcast a notification to active users.
- Notification data is stored in MongoDB and accessed through authenticated FastAPI endpoints.
- Notification reads, unread counts, and inbox pagination stay efficient as the number of notifications grows.

## Backend Implementation

### 1. Notification Model

File: `server/app/db/models/notification_model.py`

This file defines the shared notification schemas used by the backend routes, service layer, CRUD layer, and API responses.

Implemented types:

- `NotificationType`
  - Allowed values:
    - `payment`
    - `security`
    - `system`
    - `admin`

- `NotificationCreate`
  - Internal create payload for one notification.
  - Fields:
    - `user_id`
    - `title`
    - `message`
    - `type`
    - optional `action_url`
    - optional `expires_at`

- `AdminNotificationCreate`
  - Request schema for admin-created single-user notifications.
  - Extends `NotificationCreate`.

- `BroadcastNotificationCreate`
  - Request schema for broadcast notifications.
  - Fields:
    - `title`
    - `message`
    - `type`
    - optional `action_url`
    - optional `expires_at`
    - `active_users_only`

- `NotificationDB`
  - MongoDB document shape.
  - Adds:
    - `read`
    - `created_at`

- `NotificationResponse`
  - API-safe response shape.
  - Converts Mongo `_id` to string `id`.

- `NotificationListResponse`
  - Response for inbox and bell fetches.
  - Includes:
    - `notifications`
    - `unread_count`
    - `has_more`

- `NotificationMutationResponse`
  - Generic response for read/delete actions.

- `BroadcastNotificationResponse`
  - Response for broadcast creation.
  - Includes `created_count`.

Why this was implemented:

- The frontend should never receive raw MongoDB `ObjectId` values.
- Request and response contracts need to be explicit and typed.
- The notification type enum prevents unsupported notification categories from being stored.

### 2. MongoDB Collection and Indexes

File: `server/app/db/core/connection.py`

Added:

- `notifications_collection = database["notifications"]`
- `get_notifications_collection()`
- `ensure_notification_indexes(...)`
- `await ensure_notification_indexes(notifications_collection)` inside `startUp()`

Indexes:

- `("user_id", 1), ("created_at", -1)`
  - Used for loading a user's inbox in newest-first order.

- `("user_id", 1), ("read", 1)`
  - Used for unread-count queries and read-state filtering.

- `expires_at_1` TTL index with `expireAfterSeconds=0`
  - Allows MongoDB to automatically remove expired notifications.

Additional startup fix:

The first version attempted to create `expires_at_1` as a plain index. In the existing MongoDB volume, `expires_at_1` already existed as a TTL index, so backend startup failed with `IndexOptionsConflict`.

The implementation now creates the expiry index with the same TTL options:

```python
await notifications_collection.create_index(
    "expires_at",
    expireAfterSeconds=0,
    name="expires_at_1",
)
```

It also drops only a conflicting non-TTL `expires_at_1` index if one exists.

Why this was implemented:

- Inbox queries need to be efficient by user and creation date.
- Unread counts should not require scanning all user notifications.
- Expired notifications should be cleaned up by the database instead of the application.
- Startup must be idempotent across existing local Mongo volumes.

### 3. Notification CRUD Layer

File: `server/app/db/crud/notifications_crud.py`

Implemented functions:

- `create_notification(...)`
  - Inserts one notification document.
  - Returns a `NotificationResponse`.

- `create_notifications_for_users(...)`
  - Inserts one notification per target user.
  - Used by broadcast notifications.
  - Returns the number of inserted documents.

- `list_user_notifications(...)`
  - Loads active notifications for one user.
  - Sorts by `created_at` descending.
  - Uses `limit + 1` to compute `has_more`.

- `count_unread_notifications(...)`
  - Counts unread active notifications for one user.

- `mark_notification_read(...)`
  - Marks one owned notification as read.
  - Filters by both `_id` and `user_id`.

- `mark_all_notifications_read(...)`
  - Marks all unread active notifications for the current user as read.

- `delete_notification(...)`
  - Deletes one owned notification.
  - Filters by `_id` and `user_id`.

Important behavior:

- Invalid notification IDs return `400`.
- Expired notifications are excluded from list and unread-count queries.
- Ownership is enforced in update/delete operations.

Why this was implemented:

- CRUD logic stays isolated from route handlers.
- Ownership checks prevent users from modifying notifications that belong to another user.
- Pagination and unread counts are reusable by both the navbar bell and full inbox page.

### 4. Notification Service Layer

File: `server/app/db/services/notifications_service.py`

Implemented service functions:

- `get_notifications_for_user(...)`
  - Combines paginated notification loading with unread count.

- `create_admin_notification(...)`
  - Requires the current user to be an admin.
  - Validates that the target `user_id` is a valid Mongo `ObjectId`.
  - Validates that the target user exists before creating the notification.

- `broadcast_admin_notification(...)`
  - Requires the current user to be an admin.
  - Finds target users.
  - Supports `active_users_only`.
  - Creates one notification per target user.

- `mark_user_notification_read(...)`
  - Marks one current-user notification as read.
  - Returns `404` if the notification does not exist for that user.

- `mark_user_notifications_read(...)`
  - Marks all current-user notifications as read.

- `delete_user_notification(...)`
  - Deletes one current-user notification.
  - Returns `404` if the notification does not exist for that user.

Why this was implemented:

- Admin authorization and business rules belong outside raw CRUD functions.
- Direct admin sends should fail clearly if the target user does not exist.
- Route handlers stay small and focused on request/response wiring.

### 5. Notification Routes

File: `server/app/db/routes/notifications.py`

Implemented routes:

- `GET /api/notifications/?limit=20&skip=0`
  - Requires authentication.
  - Returns the current user's notifications, unread count, and pagination flag.

- `POST /api/notifications/`
  - Requires authentication.
  - Requires admin role.
  - Creates a notification for one target user.

- `POST /api/notifications/broadcast`
  - Requires authentication.
  - Requires admin role.
  - Creates notifications for multiple users.

- `PATCH /api/notifications/read-all`
  - Requires authentication.
  - Marks all current-user notifications as read.

- `PATCH /api/notifications/{notification_id}/read`
  - Requires authentication.
  - Marks one current-user notification as read.

- `DELETE /api/notifications/{notification_id}`
  - Requires authentication.
  - Deletes one current-user notification.

Why this was implemented:

- The frontend bell and inbox need a simple authenticated API surface.
- Admin notification creation should be available through protected backend endpoints.
- User mutation routes need to enforce ownership through the service/CRUD layers.

### 6. Backend Router Wiring

File: `server/main.py`

Added notification router import and route registration:

```python
from .app.db.routes import notifications, saved_quizzes, token_router

app.include_router(
    notifications.router,
    prefix="/api/notifications",
    tags=["Notifications"],
)
```

Why this was implemented:

- The route file does nothing unless it is mounted on the FastAPI application.
- Mounting under `/api/notifications` keeps the API consistent with the rest of the app.

### 7. Auth Profile Role Support

File: `server/app/auth/services.py`

Added `role` to the `/auth/profile` response.

Why this was implemented:

- The frontend admin notification page checks `user.role === "admin"`.
- Backend `UserOut` already includes `role`, but the profile serializer did not return it.
- Without this change, an admin user could be blocked by the frontend even though the backend allows admin actions.

## Frontend Implementation

### 8. Notification API Wrapper

File: `client/lib/functions/notifications.ts`

Implemented typed API helpers:

- `getNotifications({ limit, skip })`
- `markNotificationRead(notificationId)`
- `markAllNotificationsRead()`
- `deleteNotification(notificationId)`
- `createAdminNotification(payload)`
- `broadcastNotification(payload)`

Also added frontend types:

- `NotificationType`
- `NotificationItem`
- `NotificationListResponse`
- `AdminNotificationPayload`
- `BroadcastNotificationPayload`
- `BroadcastNotificationResponse`

The wrapper uses the existing authenticated Axios client from `client/lib/functions/auth.ts`.

Why this was implemented:

- Notification API access is centralized and typed.
- Components do not need to know raw endpoint URLs.
- Existing token refresh and auth behavior from the shared Axios client is reused.

### 9. Client Function Exports

File: `client/lib/functions/index.ts`

Added:

```typescript
export * from "./notifications";
```

Why this was implemented:

- Existing code imports app API helpers from the library barrel.
- Re-exporting keeps notification imports consistent with the rest of the client.

### 10. Route Constants

File: `client/constants/patterns/routes.ts`

Added:

```typescript
NOTIFICATIONS: "/notifications",
ADMIN_NOTIFICATIONS: "/admin/notifications",
```

Why this was implemented:

- Navigation should use shared route constants instead of repeated string literals.
- The bell dropdown needs a stable route to the inbox page.

### 11. User Role Type

File: `client/interfaces/models/User.ts`

Added:

```typescript
role?: "user" | "admin" | string;
```

Why this was implemented:

- The admin notification page needs to determine whether the authenticated user is an admin.
- The backend user model already supports roles.
- The frontend type needed to match the backend response.

### 12. Notification Bell Component

File: `client/components/notifications/NotificationBell.tsx`

Implemented behavior:

- Renders a bell icon for authenticated navbar usage.
- Fetches recent notifications.
- Shows unread badge.
- Polls every 60 seconds.
- Refreshes when the dropdown opens.
- Displays latest notifications in a dropdown.
- Highlights unread notifications.
- Marks a notification as read when clicked.
- Deletes notifications from the dropdown.
- Supports "Mark all read".
- Links to `/notifications`.
- Handles empty and loading states.
- Uses responsive dropdown positioning for desktop and mobile navbar placement.

Why this was implemented:

- Users need an always-visible unread notification indicator after login.
- The dropdown gives quick access without forcing navigation to the full inbox.
- Polling is a simple first version that does not require WebSockets or server-sent events.

### 13. Navbar Integration

File: `client/components/home/NavBar.tsx`

Added `NotificationBell` for authenticated users.

Desktop placement:

- Before the username and logout button.

Mobile placement:

- Inside the mobile menu after the authenticated user greeting and before logout.

Why this was implemented:

- The navbar is the main authenticated navigation surface.
- The bell should only appear for signed-in users because all notification endpoints require authentication.

### 14. User Notification Inbox Page

File: `client/pages/notifications.tsx`

Implemented page behavior:

- Protected with `RequireAuth`.
- Loads paginated notifications.
- Shows unread count.
- Supports filters:
  - `All`
  - `Unread`
  - `Read`
- Marks one notification as read.
- Marks all notifications as read.
- Deletes individual notifications.
- Supports "Load more" pagination.
- Shows empty and loading states.
- Displays `action_url` links when provided.

Why this was implemented:

- The bell dropdown is intentionally compact.
- Users need a dedicated inbox for reviewing older notifications and managing read/delete state.
- Pagination keeps the page usable as notification history grows.

### 15. Admin Notification Page

File: `client/pages/admin/notifications.tsx`

Implemented page behavior:

- Protected with `RequireAuth`.
- Shows an admin-only UI when `user.role === "admin"`.
- Blocks non-admin users with an admin access message.
- Supports two modes:
  - Broadcast
  - Single user
- Fields:
  - user ID for direct notifications
  - type
  - expires at
  - title
  - message
  - action URL
  - active users only toggle for broadcasts
- Calls:
  - `createAdminNotification(...)`
  - `broadcastNotification(...)`
- Shows created-count result for broadcasts.

Why this was implemented:

- Admins need a UI to create notifications without calling the API manually.
- Broadcast support allows operational messages to be sent to many users at once.
- Direct-user support allows targeted support/account messages.

## What Was Not Implemented

The branch does not implement login-flow notification creation.

That means:

- No "new login detected" notification is created during login.
- No login confirmation step was added.
- No password-reset or email-change notification hook was added.

Why this was left out:

- The assignment scope was navbar bell, inbox page, backend notification support confirmation, and optional admin/broadcast UI.
- Login-generated security notifications are a separate auth workflow change and can be added later without changing the core notification API.

## Startup Issue Found and Fixed

During Docker startup, the server failed before auth routes became available.

Observed error:

```text
pymongo.errors.OperationFailure: An equivalent index already exists with the same name but different options.
Requested index: { key: { expires_at: 1 }, name: "expires_at_1" }
Existing index: { key: { expires_at: 1 }, name: "expires_at_1", expireAfterSeconds: 0 }
```

Cause:

- MongoDB already had `expires_at_1` as a TTL index.
- The startup code tried to create the same named index without TTL options.
- MongoDB rejected the conflicting index definition.
- FastAPI startup failed, which made login appear broken because the backend was not running.

Fix:

- `ensure_notification_indexes(...)` now creates `expires_at_1` as a TTL index with `expireAfterSeconds=0`.
- If a non-TTL `expires_at_1` exists, it is dropped and recreated correctly.

Why this matters:

- Startup is now compatible with the existing local MongoDB data volume.
- The notification expiry behavior is explicit and consistent.
- Login/auth routes are no longer blocked by notification index creation.

## End-to-End Flow

### User Inbox Flow

1. User logs in.
2. `NavBar` renders `NotificationBell`.
3. `NotificationBell` calls `GET /api/notifications/`.
4. Backend authenticates the user through `get_current_user`.
5. Backend loads active notifications for that user's `id`.
6. Backend returns notifications, unread count, and `has_more`.
7. Bell displays unread badge and latest notifications.
8. User can mark one read, mark all read, delete, or open `/notifications`.
9. `/notifications` uses the same API wrapper for full inbox management.

### Admin Direct Notification Flow

1. Admin opens `/admin/notifications`.
2. Frontend checks `user.role`.
3. Admin selects "Single user".
4. Admin submits target `user_id`, title, message, type, and optional fields.
5. Frontend calls `POST /api/notifications/`.
6. Backend verifies the current user is admin.
7. Backend validates that the target user exists.
8. Backend inserts one notification document.
9. Target user sees the notification in the bell and inbox.

### Admin Broadcast Flow

1. Admin opens `/admin/notifications`.
2. Admin selects "Broadcast".
3. Admin submits title, message, type, optional fields, and active-user setting.
4. Frontend calls `POST /api/notifications/broadcast`.
5. Backend verifies the current user is admin.
6. Backend queries target users.
7. Backend inserts one notification per target user.
8. Response returns `created_count`.

## Verification Performed

Backend:

- `python3 -m py_compile` passed for the changed backend notification and startup files.
- Docker log analysis confirmed the startup failure was caused by notification index option conflict.
- The index creation code was updated to be idempotent with existing TTL indexes.

Frontend:

- A targeted TypeScript check passed for the notification files:
  - `NotificationBell.tsx`
  - `pages/notifications.tsx`
  - `pages/admin/notifications.tsx`
  - `lib/functions/notifications.ts`

Known unrelated tooling limitations:

- Full `tsc --noEmit` currently fails because existing tests import old component paths unrelated to this notification work.
- ESLint is blocked by a missing root `@typescript-eslint/parser` dependency in the current environment.
- Local `pytest` is not installed in the host Python environment.

## Files Added

- `server/app/db/models/notification_model.py`
- `server/app/db/crud/notifications_crud.py`
- `server/app/db/services/notifications_service.py`
- `server/app/db/routes/notifications.py`
- `client/lib/functions/notifications.ts`
- `client/components/notifications/NotificationBell.tsx`
- `client/pages/notifications.tsx`
- `client/pages/admin/notifications.tsx`
- `notification-ui-implementation.md`

## Files Modified

- `server/app/db/core/connection.py`
  - Added notification collection, getter, and indexes.
  - Fixed expiry TTL index startup conflict.

- `server/main.py`
  - Mounted notification router.

- `server/app/auth/services.py`
  - Added `role` to profile response for frontend admin gating.

- `client/lib/functions/index.ts`
  - Re-exported notification API helpers.

- `client/constants/patterns/routes.ts`
  - Added notification route constants.

- `client/interfaces/models/User.ts`
  - Added `role` to the frontend user interface.

- `client/components/home/NavBar.tsx`
  - Added notification bell for authenticated desktop and mobile navigation.
