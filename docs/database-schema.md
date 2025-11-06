# Database Schema Documentation

## Overview
The Anita backend uses Supabase (PostgreSQL) for persistent data storage. The schema includes tables for managing teachers, conversation threads, messages, Canvas course data caching, LMS connections, classes, content sources, generated content, and background jobs.

## Phase 2 Conversation Tables
The following tables were added in Phase 2 for conversation management:

## Tables

### teachers
Stores teacher profile information and Canvas authentication tokens.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique teacher identifier |
| canvas_user_id | TEXT | UNIQUE, NOT NULL | Canvas LMS user ID |
| canvas_access_token | TEXT | | Canvas API access token |
| name | TEXT | | Teacher's name |
| email | TEXT | | Teacher's email address |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Account creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Unique constraint on `canvas_user_id`

---

### threads
Stores conversation threads between teachers and Anita.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique thread identifier |
| teacher_id | UUID | FOREIGN KEY REFERENCES teachers(id) ON DELETE CASCADE | Owner of the thread |
| title | TEXT | | Thread title/summary |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Thread creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last update timestamp |

**Indexes:**
- Primary key on `id`
- `idx_threads_teacher_id` on `teacher_id`

**Relationships:**
- Belongs to `teachers` via `teacher_id`
- Has many `messages`
- Cascades delete: deleting a teacher deletes all their threads

---

### messages
Stores individual messages within conversation threads.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique message identifier |
| thread_id | UUID | FOREIGN KEY REFERENCES threads(id) ON DELETE CASCADE | Parent thread |
| role | TEXT | NOT NULL, CHECK (role IN ('user', 'assistant', 'system')) | Message sender role |
| content | TEXT | NOT NULL | Message content |
| external_id | TEXT | | Client-side message identifier (optional) |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Message timestamp |

**Indexes:**
- Primary key on `id`
- `idx_messages_thread_id` on `thread_id`

**Relationships:**
- Belongs to `threads` via `thread_id`
- Cascades delete: deleting a thread deletes all its messages

**Message Roles:**
- `user`: Messages from the teacher
- `assistant`: Messages from Anita (AI assistant)
- `system`: System-level messages/instructions

---

### courses_cache
Caches Canvas course data to reduce API calls and improve performance.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique cache entry identifier |
| teacher_id | UUID | FOREIGN KEY REFERENCES teachers(id) ON DELETE CASCADE | Teacher who owns this cache |
| canvas_course_id | TEXT | NOT NULL | Canvas course identifier |
| course_data | JSONB | NOT NULL | Cached course data as JSON |
| cached_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Cache timestamp |

**Indexes:**
- Primary key on `id`
- `idx_courses_cache_teacher_id` on `teacher_id`
- Unique constraint on `(teacher_id, canvas_course_id)`

**Relationships:**
- Belongs to `teachers` via `teacher_id`
- Cascades delete: deleting a teacher deletes all their cached course data

**Cache Strategy:**
- One cache entry per teacher per course
- JSONB format allows flexible storage of Canvas API responses
- Use `cached_at` to implement cache expiration logic

---

## Entity Relationships

```
teachers (1) ─────< threads (many)
              │
              └───< courses_cache (many)

threads (1) ──────< messages (many)
```

## Cascade Behavior
- **Delete teacher**: Automatically deletes all associated threads, messages, and course cache entries
- **Delete thread**: Automatically deletes all associated messages

## Existing Tables (Pre-Phase 2)
The database also includes these tables from earlier development:
- **lms_connections**: LMS integration configurations
- **classes**: Course/class information
- **content_sources**: Educational content sources
- **generated_content**: AI-generated teaching materials
- **jobs**: Background job tracking

## Migration Files
- `migrations/001_initial_schema.sql` - Initial schema (not applied - superseded by existing schema)
- `migrations/002_add_conversation_tables.sql` - Added threads, messages, and courses_cache tables

## Connection Configuration
- Connection setup in `config/supabase_config.py`
- Environment variables: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`

## Service Layer
Database operations are abstracted through service modules:
- `services/teacher_service.py` - Teacher CRUD operations
- `services/thread_service.py` - Thread management
- `services/message_service.py` - Message operations
