# Thread Storage & LLM Runner Review

## Overview

This document outlines the review and testing plan for thread storage and the LLM runner implementation in the Anita backend. Based on the Thesys C1 SDK documentation, we'll verify that our implementation follows best practices.

---

## Current Implementation Status

### What's Working ✅

Our current implementation (`llm_runner.py`, `thread_service.py`, `message_service.py`) includes:

- ✅ Using Thesys C1 API correctly (OpenAI client + C1 model)
- ✅ Using `@with_c1_response()` decorator for FastAPI streaming
- ✅ Storing messages in Supabase (PostgreSQL)
- ✅ Loading conversation history before API call
- ✅ Saving both user and assistant messages
- ✅ Using `write_content()` for streaming chunks
- ✅ Using `get_assistant_message()` to get complete response
- ✅ Storing message IDs (`external_id`)

### Architecture

```
Client Request
    ↓
POST /chat (main.py)
    ↓
generate_stream() (llm_runner.py)
    ↓
1. Load messages from DB (message_service)
2. Format for OpenAI API
3. Add new user message
4. Save user message to DB
5. Call Thesys C1 API
6. Stream response with write_content()
7. Get complete response with get_assistant_message()
8. Save assistant message to DB
```

---

## Thesys Best Practices Checklist

According to Thesys documentation ([`persistence.md`](../docs/thesys/guides/conversational/persistence.md) and [`backend-api.md`](../docs/thesys/guides/conversational/backend-api.md)), we should:

### Message Storage Requirements

- [x] Store ALL messages (user, assistant, system)
- [x] Include message IDs for future updates
- [ ] Store tool call messages (even if not displayed) - **TODO: Verify if needed**
- [x] Accumulate complete response before saving
- [x] Use proper streaming functions

### Message Format

Our messages table schema:
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    external_id TEXT,  -- Client-side message IDs
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Thesys Recommended:**
```typescript
interface Message {
  id: string;              // ✅ We have as external_id
  role: string;            // ✅ We have
  content: string;         // ✅ We have
  timestamp: Date;         // ✅ We have as created_at
  tool_calls?: any[];      // ❓ Not implemented - may not be needed
  metadata?: Record<string, any>;  // ❓ Could add as JSONB
}
```

---

## Current Implementation Analysis

### llm_runner.py

```python
async def generate_stream(chat_request: ChatRequest):
    # 1. Load conversation history from database ✅
    db_messages = message_service.get_thread_messages(chat_request.threadId)

    # 2. Convert to OpenAI format ✅
    conversation_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in db_messages
    ]

    # 3. Add new user message ✅
    conversation_history.append(chat_request.prompt)

    # 4. Save user message to DB ✅
    message_service.create_message(
        thread_id=chat_request.threadId,
        role=chat_request.prompt['role'],
        content=chat_request.prompt['content'],
        external_id=chat_request.prompt['id']
    )

    # 5. Call Thesys C1 API ✅
    stream = client.chat.completions.create(
        messages=conversation_history,
        model="c1/anthropic/claude-sonnet-4/v-20250815",
        stream=True,
    )

    # 6. Stream chunks to client ✅
    for chunk in stream:
        if delta and delta.content:
            await write_content(delta.content)

        # 7. Get complete response ✅
        if finish_reason:
            assistant_message_for_history = get_assistant_message()

    # 8. Save assistant response ✅
    if assistant_message_for_history:
        message_service.create_message(
            thread_id=chat_request.threadId,
            role=assistant_message_for_history['role'],
            content=assistant_message_for_history['content'],
            external_id=chat_request.responseId
        )
```

**Key Questions:**
1. Does `get_assistant_message()` capture the full accumulated response? **NEEDS TESTING**
2. Are we handling tool calls if the C1 agent uses Canvas MCP? **NEEDS INVESTIGATION**
3. Do we need to store any additional metadata? **DECIDE**

---

## Testing Plan

### Test 1: Basic Message Storage (5 min)

**Goal:** Verify messages are stored correctly in Supabase

```bash
# Send a test message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "role": "user",
      "content": "Hello! What is 2+2?",
      "id": "msg-001"
    },
    "threadId": "test-thread-123",
    "responseId": "resp-001"
  }'
```

**Verify in Supabase:**
1. Check `threads` table has `test-thread-123`
2. Check `messages` table has 2 messages:
   - User message: `external_id="msg-001"`, `content="Hello! What is 2+2?"`
   - Assistant message: `external_id="resp-001"`, content with the answer

---

### Test 2: Conversation History (10 min)

**Goal:** Verify conversation context is maintained

```bash
# Send first message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "role": "user",
      "content": "My name is Alice",
      "id": "msg-101"
    },
    "threadId": "test-thread-456",
    "responseId": "resp-101"
  }'

# Wait for response, then send follow-up
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "role": "user",
      "content": "What is my name?",
      "id": "msg-102"
    },
    "threadId": "test-thread-456",
    "responseId": "resp-102"
  }'
```

**Expected Result:**
- Assistant should remember "Alice" from previous message
- If it doesn't, conversation history isn't loading correctly

**Verify in Supabase:**
- Should have 4 messages in `test-thread-456`
- Messages should be in chronological order

---

### Test 3: Multiple Threads (5 min)

**Goal:** Verify thread isolation

```bash
# Thread A
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {"role": "user", "content": "I like pizza", "id": "a1"},
    "threadId": "thread-a",
    "responseId": "resp-a1"
  }'

# Thread B
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {"role": "user", "content": "I like pasta", "id": "b1"},
    "threadId": "thread-b",
    "responseId": "resp-b1"
  }'

# Thread A follow-up
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {"role": "user", "content": "What do I like?", "id": "a2"},
    "threadId": "thread-a",
    "responseId": "resp-a2"
  }'
```

**Expected Result:**
- Thread A should respond "pizza"
- Thread B context should not leak into Thread A

---

### Test 4: Long Response Accumulation (5 min)

**Goal:** Verify `get_assistant_message()` captures full response

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "role": "user",
      "content": "Write me a 500 word essay about Python programming",
      "id": "msg-201"
    },
    "threadId": "test-thread-789",
    "responseId": "resp-201"
  }'
```

**Verify:**
1. Stream should show progressive content
2. Final message in DB should contain complete essay (not truncated)
3. Check character count matches what was streamed

---

### Test 5: Error Handling (5 min)

**Goal:** Verify graceful error handling

```bash
# Missing threadId
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {"role": "user", "content": "Test", "id": "e1"},
    "responseId": "resp-e1"
  }'

# Invalid thread format
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {"role": "user", "content": "Test", "id": "e2"},
    "threadId": null,
    "responseId": "resp-e2"
  }'
```

**Expected:**
- Should return proper HTTP error codes (400/422)
- Should not crash the server
- Should not create invalid DB entries

---

## Database Verification Queries

After running tests, check Supabase with these queries:

```sql
-- List all threads
SELECT id, teacher_id, title, created_at, updated_at
FROM threads
ORDER BY created_at DESC;

-- View messages for a specific thread
SELECT id, role, LEFT(content, 100) as content_preview, external_id, created_at
FROM messages
WHERE thread_id = 'test-thread-123'
ORDER BY created_at ASC;

-- Count messages per thread
SELECT thread_id, COUNT(*) as message_count
FROM messages
GROUP BY thread_id
ORDER BY message_count DESC;

-- Find orphaned messages (if any)
SELECT m.*
FROM messages m
LEFT JOIN threads t ON m.thread_id = t.id
WHERE t.id IS NULL;
```

---

## Known Gaps & Future Improvements

### 1. Tool Call Messages

**Current State:** Not implemented

**From Thesys Docs:**
> Store tool call messages even if not displayed to users

**Question:** Does the C1 agent use Canvas MCP tools during conversation?

**Action Items:**
- [ ] Test with a prompt that requires Canvas data (e.g., "Show me my courses")
- [ ] Check if tool calls appear in the stream
- [ ] Determine if we need to store tool_calls in messages table
- [ ] Consider adding `metadata JSONB` column for tool calls

### 2. Message Updates

**Current State:** We have `external_id` but no update endpoint

**From Thesys Docs:**
> Response IDs are essential for future updates, required for form handling

**Action Items:**
- [ ] Add `update_message()` function to message_service
- [ ] Create `PATCH /messages/{id}` endpoint (if needed)
- [ ] Document when message updates are needed

### 3. Thread Titles

**Current State:** Threads have a `title` field, but it's not auto-generated

**Improvement:**
- [ ] Auto-generate title from first user message
- [ ] Add endpoint to update thread title
- [ ] Add "New Conversation" as default title

### 4. Thread Management API

**Current State:** No REST endpoints for thread CRUD operations

**Needed Endpoints:**
```
GET    /threads              - List user's threads
GET    /threads/{id}         - Get thread details
POST   /threads              - Create new thread
PATCH  /threads/{id}         - Update thread (title)
DELETE /threads/{id}         - Delete thread
GET    /threads/{id}/messages - Get messages for thread
```

**Action Items:**
- [ ] Create `routers/thread_router.py`
- [ ] Implement thread CRUD endpoints
- [ ] Add to main.py router

### 5. Production Readiness

**Missing:**
- [ ] Rate limiting on `/chat` endpoint
- [ ] Input validation/sanitization
- [ ] Proper error responses with error codes
- [ ] Logging for debugging
- [ ] Monitoring/metrics

---

## Comparison: Current vs. Thesys Recommendation

### Our Implementation (FastAPI + Supabase)

```python
# llm_runner.py
client = OpenAI(
    api_key=os.getenv("THESYS_API_KEY"),
    base_url="https://api.thesys.dev/v1/embed",
)

# Load from database
db_messages = message_service.get_thread_messages(threadId)
conversation_history = [
    {"role": msg["role"], "content": msg["content"]}
    for msg in db_messages
]

# Stream response
stream = client.chat.completions.create(
    messages=conversation_history,
    model="c1/anthropic/claude-sonnet-4/v-20250815",
    stream=True,
)

# Save to database
message_service.create_message(
    thread_id=threadId,
    role='assistant',
    content=assistant_message_for_history['content'],
    external_id=responseId
)
```

### Thesys Example (Next.js + Firebase)

```typescript
// Backend API
const messages = await getLLMThreadMessages(threadId);

const stream = await client.chat.completions.create({
  model: 'c1/anthropic/claude-sonnet-4/v-20250617',
  messages,
  stream: true
});

const transformedStream = streamToC1Response(stream, {
  onComplete: async () => {
    await addMessages(threadId, [{
      id: responseId,
      role: 'assistant',
      content: accumulatedContent
    }]);
  }
});
```

**Key Differences:**
- ✅ We use same OpenAI client
- ✅ We use same model (slightly different version)
- ✅ We load messages from DB
- ✅ We save messages to DB
- ⚠️ We use `@with_c1_response()` decorator instead of `streamToC1Response()`
- ⚠️ We use `get_assistant_message()` instead of manual accumulation

**Questions:**
- Does `@with_c1_response()` work the same as `streamToC1Response()`?
- Is `get_assistant_message()` equivalent to accumulating content?

---

## Next Steps

### Immediate (This Session)

1. **Run Tests 1-5** and document results
2. **Verify** message storage is working correctly
3. **Check** if conversation history loads properly
4. **Identify** any bugs or issues

### Short Term (Next Session)

1. **Add Thread Management API** (routers/thread_router.py)
2. **Implement** auto-generated thread titles
3. **Add** proper error handling and validation
4. **Test** with Canvas MCP integration (if tool calls needed)

### Medium Term (Future Epics)

1. **Add** message update functionality
2. **Implement** rate limiting
3. **Add** comprehensive logging
4. **Create** monitoring/metrics
5. **Write** integration tests

---

## Testing Session Template

Use this template to document your testing session:

```markdown
## Test Session: [DATE]

### Environment
- Backend URL: http://localhost:8000
- Supabase Project: [PROJECT_ID]
- Model: c1/anthropic/claude-sonnet-4/v-20250815

### Test 1: Basic Message Storage
- [ ] Sent test message
- [ ] Verified thread created
- [ ] Verified user message stored
- [ ] Verified assistant message stored
- **Result:** [PASS/FAIL]
- **Notes:**

### Test 2: Conversation History
- [ ] Sent first message with name
- [ ] Sent follow-up asking for name
- [ ] Assistant remembered name
- **Result:** [PASS/FAIL]
- **Notes:**

### Test 3: Multiple Threads
- [ ] Created thread A
- [ ] Created thread B
- [ ] Verified isolation
- **Result:** [PASS/FAIL]
- **Notes:**

### Test 4: Long Response
- [ ] Requested long response
- [ ] Verified streaming worked
- [ ] Verified complete content saved
- **Result:** [PASS/FAIL]
- **Notes:**

### Test 5: Error Handling
- [ ] Tested missing threadId
- [ ] Tested invalid input
- [ ] Verified error responses
- **Result:** [PASS/FAIL]
- **Notes:**

### Issues Found
1. [Issue description]
2. [Issue description]

### Action Items
- [ ] [Action item]
- [ ] [Action item]
```

---

## References

- **Thesys Docs Index:** `/docs/thesys/INDEX.md`
- **Persistence Guide:** `/docs/thesys/guides/conversational/persistence.md`
- **Backend API Guide:** `/docs/thesys/guides/conversational/backend-api.md`
- **Current Implementation:**
  - `llm_runner.py`
  - `services/thread_service.py`
  - `services/message_service.py`
  - `main.py`
