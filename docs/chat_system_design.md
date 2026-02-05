# Library DBMS – Chatroom System Design

## Purpose
A chat system inside the library where:
- Students discuss books.
- Librarians post announcements.
- Study groups chat privately.
- Users can stay anonymous.

## Core Features
1. **Anonymous Users**: Real identity hidden; mapped to generated `anon_id`.
2. **Room Types**: Public, Private (Invite-only), Study Group, Librarian Room (Announcement).
3. **Invitation System**: Expires after time/usage.
4. **Roles**: Admin, Moderator, Member, Librarian.
5. **Message Control**: Soft delete, Timestamped, Securely stored.

## Database Structure

### USERS (Existing)
* `user_id` (PK), `name`, `email`, `role`

### CHAT_ANON_ID
* `anon_id` (PK, VARCHAR)
* `user_id` (FK)
* `created_at`
* `is_active`

### CHAT_ROOMS
* `room_id` (PK)
* `room_name`
* `room_type` (public, private, study, librarian)
* `created_by` (FK -> user_id? or anon_id?) -> *Decision: Real user_id for accountability*
* `is_active`
* `created_at`

### ROOM_MEMBERS
* `room_id` (FK)
* `anon_id` (FK)
* `role` (admin, member, mod)
* `joined_at`
* `is_muted`

### ROOM_INVITES
* `invite_code` (PK)
* `room_id` (FK)
* `created_by`
* `expires_at`
* `max_uses`
* `uses_count`

### CHAT_MESSAGES
* `message_id` (PK)
* `room_id` (FK)
* `anon_id` (FK)
* `message_text`
* `sent_at`
* `is_deleted` (Soft delete)

## Chat Flow
1. **Join**: User login -> Generate/Fetch `anon_id` -> Chat UI.
2. **Create Room**: User creates room -> Becomes Admin.
3. **Invite**: Admin generates code -> User enters code -> Added to `ROOM_MEMBERS`.
4. **Message**: `anon_id` sends to `room_id` -> Broadcast.
5. **Moderation**: Admin sets `is_deleted=TRUE`.

## Security & Privacy
- **Access Control**: Room-based auth, Invite validation.
- **Privacy**: No real user IDs in public chat APIs.
- **Communication**: WebSocket (secure).

## Implementation Plan

### Phase 1: Database Migration
- Create new tables: `chat_anon_id`, `chat_rooms`, `room_members`, `room_invites`, `chat_messages`.
- Verify foreign keys.

### Phase 2: Backend Logic
- `chat_service.py`: Handle anonymity generation, room creation, inviting.
- `socket_service.py`: Update to support new schema and room types.

### Phase 3: Frontend UI
- Update Chat Interface (`community.html` or new `chat.html`).
- Add "Create Room" modal.
- Add "Join via Code" modal.
- Display Generic/Anon Names.

### Phase 4: Integration
- Link Study Groups to Books (Optional Advanced).
- Real-time updates.
