# Conversational Persistence Guide

## Overview

Conversational persistence enables you to store and retrieve chat threads and message history, allowing users to maintain seamless conversations across different sessions. This guide covers implementing persistent conversation storage using Firebase Firestore in a Next.js application with the Thesys C1 SDK.

## What is Conversational Persistence?

Conversational persistence is the ability to:
- **Save conversation history** across sessions
- **Retrieve past conversations** for context
- **Manage multiple conversation threads**
- **Maintain state** between user interactions
- **Enable conversation continuity** even after page refreshes or app restarts

### Benefits

- **📝 Conversation History**: Users can review past interactions
- **🔄 Session Continuity**: Pick up conversations where they left off
- **🗂️ Thread Management**: Organize multiple conversation topics
- **💾 Reliable Storage**: Persistent backend storage
- **🚀 Better UX**: Seamless multi-session experience

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                 │
│  ┌─────────────────────────────────────────────┐   │
│  │         C1Chat / C1Component                 │   │
│  │  - Display messages                          │   │
│  │  - Handle user input                         │   │
│  │  - Manage thread selection                   │   │
│  └──────────────────┬──────────────────────────┘   │
│                     │                                │
│  ┌──────────────────▼──────────────────────────┐   │
│  │         Thread Service Layer                 │   │
│  │  - createThread()                            │   │
│  │  - addMessages()                             │   │
│  │  - getThreadList()                           │   │
│  │  - getMessages()                             │   │
│  └──────────────────┬──────────────────────────┘   │
└────────────────────┬┬───────────────────────────────┘
                     ││ API Calls
                     ▼▼
┌─────────────────────────────────────────────────────┐
│              Backend API Routes                      │
│  - POST /api/chat (fetch history, save messages)    │
│  - GET /api/threads (list threads)                   │
│  - POST /api/threads (create thread)                 │
└──────────────────────┬──────────────────────────────┘
                       │ Database Operations
                       ▼
┌─────────────────────────────────────────────────────┐
│              Firebase Firestore                      │
│  Collections:                                        │
│  - threads (conversation metadata)                   │
│  - messages (conversation history)                   │
└─────────────────────────────────────────────────────┘
```

## Prerequisites

### Required Packages

**Frontend:**
```bash
npm install @thesysai/genui-sdk @crayonai/react-ui firebase
```

**Backend (Python):**
```bash
pip install firebase-admin thesys_genui_sdk
```

### Firebase Setup

1. Create a Firebase project at [https://console.firebase.google.com](https://console.firebase.google.com)
2. Enable Firestore Database
3. Get your Firebase configuration
4. Set up authentication (optional but recommended)

## Implementation

### Step 1: Firebase Configuration

#### Frontend Configuration (Next.js)

```typescript
// lib/firebase.ts
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firestore
export const db = getFirestore(app);
```

**Environment Variables (.env.local):**
```bash
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
```

#### Backend Configuration (Python)

```python
# backend/firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase Admin SDK
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
})

firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()
```

**Environment Variables (.env):**
```bash
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your_client_id
```

### Step 2: Create Thread Service Layer

#### TypeScript Implementation

```typescript
// services/threadService.ts
import {
  collection,
  doc,
  addDoc,
  getDoc,
  getDocs,
  updateDoc,
  query,
  where,
  orderBy,
  serverTimestamp,
  Timestamp
} from 'firebase/firestore';
import { db } from '@/lib/firebase';

export interface Thread {
  id: string;
  title: string;
  userId: string;
  createdAt: Timestamp;
  updatedAt: Timestamp;
  metadata?: Record<string, any>;
}

export interface Message {
  id: string;
  threadId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  createdAt: Timestamp;
  metadata?: Record<string, any>;
}

/**
 * Create a new conversation thread
 */
export async function createThread(
  userId: string,
  title: string = 'New Conversation',
  metadata?: Record<string, any>
): Promise<Thread> {
  const threadData = {
    title,
    userId,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
    metadata: metadata || {}
  };

  const docRef = await addDoc(collection(db, 'threads'), threadData);

  return {
    id: docRef.id,
    ...threadData,
    createdAt: Timestamp.now(),
    updatedAt: Timestamp.now()
  } as Thread;
}

/**
 * Get list of threads for a user
 */
export async function getThreadList(userId: string): Promise<Thread[]> {
  const q = query(
    collection(db, 'threads'),
    where('userId', '==', userId),
    orderBy('updatedAt', 'desc')
  );

  const querySnapshot = await getDocs(q);
  const threads: Thread[] = [];

  querySnapshot.forEach((doc) => {
    threads.push({
      id: doc.id,
      ...doc.data()
    } as Thread);
  });

  return threads;
}

/**
 * Get a specific thread by ID
 */
export async function getThread(threadId: string): Promise<Thread | null> {
  const docRef = doc(db, 'threads', threadId);
  const docSnap = await getDoc(docRef);

  if (!docSnap.exists()) {
    return null;
  }

  return {
    id: docSnap.id,
    ...docSnap.data()
  } as Thread;
}

/**
 * Add messages to a thread
 */
export async function addMessages(
  threadId: string,
  messages: Omit<Message, 'id' | 'threadId' | 'createdAt'>[]
): Promise<Message[]> {
  const savedMessages: Message[] = [];

  for (const message of messages) {
    const messageData = {
      threadId,
      role: message.role,
      content: message.content,
      createdAt: serverTimestamp(),
      metadata: message.metadata || {}
    };

    const docRef = await addDoc(collection(db, 'messages'), messageData);

    savedMessages.push({
      id: docRef.id,
      ...messageData,
      createdAt: Timestamp.now()
    } as Message);
  }

  // Update thread's updatedAt timestamp
  await updateDoc(doc(db, 'threads', threadId), {
    updatedAt: serverTimestamp()
  });

  return savedMessages;
}

/**
 * Get all messages for a thread
 */
export async function getMessages(threadId: string): Promise<Message[]> {
  const q = query(
    collection(db, 'messages'),
    where('threadId', '==', threadId),
    orderBy('createdAt', 'asc')
  );

  const querySnapshot = await getDocs(q);
  const messages: Message[] = [];

  querySnapshot.forEach((doc) => {
    messages.push({
      id: doc.id,
      ...doc.data()
    } as Message);
  });

  return messages;
}

/**
 * Update thread title
 */
export async function updateThreadTitle(
  threadId: string,
  title: string
): Promise<void> {
  await updateDoc(doc(db, 'threads', threadId), {
    title,
    updatedAt: serverTimestamp()
  });
}

/**
 * Delete a thread and all its messages
 */
export async function deleteThread(threadId: string): Promise<void> {
  // Delete all messages in the thread
  const messages = await getMessages(threadId);
  for (const message of messages) {
    await deleteDoc(doc(db, 'messages', message.id));
  }

  // Delete the thread
  await deleteDoc(doc(db, 'threads', threadId));
}
```

#### Python Implementation

```python
# backend/services/thread_service.py
from datetime import datetime
from typing import List, Dict, Optional
from firebase_admin import firestore
from backend.firebase_config import db

class Thread:
    def __init__(self, id: str, title: str, user_id: str,
                 created_at: datetime, updated_at: datetime,
                 metadata: Dict = None):
        self.id = id
        self.title = title
        self.user_id = user_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.metadata = metadata or {}

class Message:
    def __init__(self, id: str, thread_id: str, role: str,
                 content: str, created_at: datetime,
                 metadata: Dict = None):
        self.id = id
        self.thread_id = thread_id
        self.role = role
        self.content = content
        self.created_at = created_at
        self.metadata = metadata or {}

def create_thread(user_id: str, title: str = "New Conversation",
                  metadata: Dict = None) -> Thread:
    """Create a new conversation thread"""
    thread_data = {
        'title': title,
        'user_id': user_id,
        'created_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP,
        'metadata': metadata or {}
    }

    doc_ref = db.collection('threads').add(thread_data)
    thread_id = doc_ref[1].id

    return Thread(
        id=thread_id,
        title=title,
        user_id=user_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        metadata=metadata
    )

def get_thread_list(user_id: str) -> List[Thread]:
    """Get list of threads for a user"""
    threads_ref = db.collection('threads')
    query = threads_ref.where('user_id', '==', user_id)\
                       .order_by('updated_at', direction=firestore.Query.DESCENDING)

    threads = []
    for doc in query.stream():
        data = doc.to_dict()
        threads.append(Thread(
            id=doc.id,
            title=data['title'],
            user_id=data['user_id'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            metadata=data.get('metadata', {})
        ))

    return threads

def get_thread(thread_id: str) -> Optional[Thread]:
    """Get a specific thread by ID"""
    doc_ref = db.collection('threads').document(thread_id)
    doc = doc_ref.get()

    if not doc.exists:
        return None

    data = doc.to_dict()
    return Thread(
        id=doc.id,
        title=data['title'],
        user_id=data['user_id'],
        created_at=data['created_at'],
        updated_at=data['updated_at'],
        metadata=data.get('metadata', {})
    )

def add_messages(thread_id: str, messages: List[Dict]) -> List[Message]:
    """Add messages to a thread"""
    saved_messages = []

    for message in messages:
        message_data = {
            'thread_id': thread_id,
            'role': message['role'],
            'content': message['content'],
            'created_at': firestore.SERVER_TIMESTAMP,
            'metadata': message.get('metadata', {})
        }

        doc_ref = db.collection('messages').add(message_data)
        message_id = doc_ref[1].id

        saved_messages.append(Message(
            id=message_id,
            thread_id=thread_id,
            role=message['role'],
            content=message['content'],
            created_at=datetime.now(),
            metadata=message.get('metadata', {})
        ))

    # Update thread's updated_at timestamp
    db.collection('threads').document(thread_id).update({
        'updated_at': firestore.SERVER_TIMESTAMP
    })

    return saved_messages

def get_messages(thread_id: str) -> List[Message]:
    """Get all messages for a thread"""
    messages_ref = db.collection('messages')
    query = messages_ref.where('thread_id', '==', thread_id)\
                        .order_by('created_at', direction=firestore.Query.ASCENDING)

    messages = []
    for doc in query.stream():
        data = doc.to_dict()
        messages.append(Message(
            id=doc.id,
            thread_id=data['thread_id'],
            role=data['role'],
            content=data['content'],
            created_at=data['created_at'],
            metadata=data.get('metadata', {})
        ))

    return messages

def update_thread_title(thread_id: str, title: str) -> None:
    """Update thread title"""
    db.collection('threads').document(thread_id).update({
        'title': title,
        'updated_at': firestore.SERVER_TIMESTAMP
    })

def delete_thread(thread_id: str) -> None:
    """Delete a thread and all its messages"""
    # Delete all messages
    messages = get_messages(thread_id)
    for message in messages:
        db.collection('messages').document(message.id).delete()

    # Delete thread
    db.collection('threads').document(thread_id).delete()
```

### Step 3: Backend API Integration

#### Next.js API Route

```typescript
// app/api/chat/route.ts
import { NextRequest } from 'next/server';
import OpenAI from 'openai';
import { getMessages, addMessages } from '@/services/threadService';

const client = new OpenAI({
  baseURL: 'https://api.thesys.dev/v1/embed',
  apiKey: process.env.THESYS_API_KEY
});

export async function POST(req: NextRequest) {
  try {
    const { threadId, message, userId } = await req.json();

    // 1. Fetch historical messages from Firestore
    const historicalMessages = await getMessages(threadId);

    // 2. Convert to OpenAI format
    const messages = historicalMessages.map(msg => ({
      role: msg.role,
      content: msg.content
    }));

    // 3. Add new user message
    messages.push({
      role: 'user',
      content: message
    });

    // 4. Call C1 API
    const response = await client.chat.completions.create({
      model: 'gpt-4',
      messages: [
        {
          role: 'system',
          content: 'You are a helpful assistant.'
        },
        ...messages
      ],
      stream: true
    });

    // 5. Stream response and collect full content
    const stream = response.toReadableStream();
    let fullResponse = '';

    // Create a transform stream to capture the response
    const transformStream = new TransformStream({
      async transform(chunk, controller) {
        const text = new TextDecoder().decode(chunk);
        fullResponse += text;
        controller.enqueue(chunk);
      },
      async flush() {
        // 6. Save messages to Firestore after streaming completes
        await addMessages(threadId, [
          { role: 'user', content: message },
          { role: 'assistant', content: fullResponse }
        ]);
      }
    });

    return new Response(stream.pipeThrough(transformStream), {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
      }
    });

  } catch (error) {
    console.error('Chat error:', error);
    return Response.json({ error: 'Failed to process chat' }, { status: 500 });
  }
}
```

#### Python FastAPI Implementation

```python
# backend/api/chat.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel
from backend.services.thread_service import get_messages, add_messages
import os

router = APIRouter()

client = OpenAI(
    base_url='https://api.thesys.dev/v1/embed',
    api_key=os.getenv('THESYS_API_KEY')
)

class ChatRequest(BaseModel):
    thread_id: str
    message: str
    user_id: str

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        # 1. Fetch historical messages
        historical_messages = get_messages(request.thread_id)

        # 2. Convert to OpenAI format
        messages = [
            {'role': msg.role, 'content': msg.content}
            for msg in historical_messages
        ]

        # 3. Add new user message
        messages.append({
            'role': 'user',
            'content': request.message
        })

        # 4. Call C1 API
        response = client.chat.completions.create(
            model='gpt-4',
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                *messages
            ],
            stream=True
        )

        # 5. Stream response and save
        async def generate():
            full_response = ''
            try:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield content

                # 6. Save messages after streaming
                add_messages(request.thread_id, [
                    {'role': 'user', 'content': request.message},
                    {'role': 'assistant', 'content': full_response}
                ])
            except Exception as e:
                print(f"Error during streaming: {e}")

        return StreamingResponse(generate(), media_type='text/event-stream')

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 4: Frontend Integration

#### Thread Management Component

```typescript
// components/ThreadList.tsx
'use client';

import { useState, useEffect } from 'react';
import { getThreadList, createThread, Thread } from '@/services/threadService';

interface ThreadListProps {
  userId: string;
  onThreadSelect: (threadId: string) => void;
  selectedThreadId?: string;
}

export default function ThreadList({
  userId,
  onThreadSelect,
  selectedThreadId
}: ThreadListProps) {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadThreads();
  }, [userId]);

  async function loadThreads() {
    try {
      const threadList = await getThreadList(userId);
      setThreads(threadList);
    } catch (error) {
      console.error('Failed to load threads:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateThread() {
    try {
      const newThread = await createThread(userId);
      setThreads([newThread, ...threads]);
      onThreadSelect(newThread.id);
    } catch (error) {
      console.error('Failed to create thread:', error);
    }
  }

  if (loading) {
    return <div>Loading threads...</div>;
  }

  return (
    <div className="thread-list">
      <button onClick={handleCreateThread} className="new-thread-btn">
        + New Conversation
      </button>

      <div className="threads">
        {threads.map((thread) => (
          <div
            key={thread.id}
            className={`thread-item ${selectedThreadId === thread.id ? 'active' : ''}`}
            onClick={() => onThreadSelect(thread.id)}
          >
            <h4>{thread.title}</h4>
            <p>{thread.updatedAt.toDate().toLocaleDateString()}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

#### Chat Component with Persistence

```typescript
// components/PersistentChat.tsx
'use client';

import { useState, useEffect } from 'react';
import { C1Chat } from '@thesysai/genui-sdk';
import { getMessages, Message } from '@/services/threadService';
import ThreadList from './ThreadList';

interface PersistentChatProps {
  userId: string;
}

export default function PersistentChat({ userId }: PersistentChatProps) {
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [initialMessages, setInitialMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedThreadId) {
      loadMessages();
    }
  }, [selectedThreadId]);

  async function loadMessages() {
    if (!selectedThreadId) return;

    setLoading(true);
    try {
      const messages = await getMessages(selectedThreadId);
      setInitialMessages(messages);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setLoading(false);
    }
  }

  function handleThreadSelect(threadId: string) {
    setSelectedThreadId(threadId);
  }

  return (
    <div className="persistent-chat">
      <div className="sidebar">
        <ThreadList
          userId={userId}
          onThreadSelect={handleThreadSelect}
          selectedThreadId={selectedThreadId || undefined}
        />
      </div>

      <div className="chat-area">
        {selectedThreadId ? (
          loading ? (
            <div>Loading messages...</div>
          ) : (
            <C1Chat
              apiEndpoint={`/api/chat?threadId=${selectedThreadId}&userId=${userId}`}
              initialMessages={initialMessages.map(msg => ({
                role: msg.role,
                content: msg.content
              }))}
              systemPrompt="You are a helpful assistant."
            />
          )
        ) : (
          <div className="no-thread-selected">
            <p>Select a conversation or create a new one</p>
          </div>
        )}
      </div>
    </div>
  );
}
```

## Best Practices

### 1. Security

**Use Firestore Security Rules:**
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Threads: Users can only access their own threads
    match /threads/{threadId} {
      allow read, write: if request.auth != null &&
                           request.auth.uid == resource.data.userId;
      allow create: if request.auth != null &&
                      request.auth.uid == request.resource.data.userId;
    }

    // Messages: Users can only access messages in their threads
    match /messages/{messageId} {
      allow read: if request.auth != null &&
                    get(/databases/$(database)/documents/threads/$(resource.data.threadId)).data.userId == request.auth.uid;
      allow create: if request.auth != null &&
                      get(/databases/$(database)/documents/threads/$(request.resource.data.threadId)).data.userId == request.auth.uid;
    }
  }
}
```

**Never use test mode in production!**

### 2. Error Handling

```typescript
async function addMessagesWithRetry(
  threadId: string,
  messages: any[],
  maxRetries = 3
): Promise<Message[]> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await addMessages(threadId, messages);
    } catch (error) {
      if (attempt === maxRetries) {
        console.error('Failed to save messages after retries:', error);
        throw error;
      }
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
    }
  }
  throw new Error('Unexpected error in retry logic');
}
```

### 3. Message Metadata

Store useful metadata with messages:

```typescript
await addMessages(threadId, [
  {
    role: 'user',
    content: message,
    metadata: {
      timestamp: Date.now(),
      ipAddress: req.headers.get('x-forwarded-for'),
      userAgent: req.headers.get('user-agent'),
      model: 'gpt-4'
    }
  }
]);
```

### 4. Thread Titles

Auto-generate meaningful thread titles:

```typescript
async function generateThreadTitle(firstMessage: string): Promise<string> {
  const response = await client.chat.completions.create({
    model: 'gpt-4',
    messages: [
      {
        role: 'system',
        content: 'Generate a short, concise title (max 50 chars) for this conversation.'
      },
      {
        role: 'user',
        content: firstMessage
      }
    ]
  });

  return response.choices[0].message.content.substring(0, 50);
}
```

### 5. Pagination

Implement pagination for large message histories:

```typescript
export async function getMessagesPaginated(
  threadId: string,
  limit: number = 50,
  lastMessageId?: string
): Promise<{ messages: Message[]; hasMore: boolean }> {
  let q = query(
    collection(db, 'messages'),
    where('threadId', '==', threadId),
    orderBy('createdAt', 'desc'),
    limit(limit + 1)
  );

  if (lastMessageId) {
    const lastDoc = await getDoc(doc(db, 'messages', lastMessageId));
    q = query(q, startAfter(lastDoc));
  }

  const querySnapshot = await getDocs(q);
  const messages: Message[] = [];

  querySnapshot.forEach((doc) => {
    messages.push({ id: doc.id, ...doc.data() } as Message);
  });

  const hasMore = messages.length > limit;
  if (hasMore) messages.pop();

  return { messages: messages.reverse(), hasMore };
}
```

## Alternative Storage Options

### PostgreSQL

```typescript
// Using Prisma
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function createThread(userId: string, title: string) {
  return await prisma.thread.create({
    data: { userId, title }
  });
}

export async function addMessages(threadId: string, messages: any[]) {
  return await prisma.message.createMany({
    data: messages.map(msg => ({
      threadId,
      role: msg.role,
      content: msg.content
    }))
  });
}
```

### MongoDB

```typescript
// Using MongoDB Node.js driver
import { MongoClient } from 'mongodb';

const client = new MongoClient(process.env.MONGODB_URI);
const db = client.db('chat');

export async function createThread(userId: string, title: string) {
  const result = await db.collection('threads').insertOne({
    userId,
    title,
    createdAt: new Date(),
    updatedAt: new Date()
  });

  return { id: result.insertedId.toString(), userId, title };
}

export async function addMessages(threadId: string, messages: any[]) {
  return await db.collection('messages').insertMany(
    messages.map(msg => ({
      threadId,
      role: msg.role,
      content: msg.content,
      createdAt: new Date()
    }))
  );
}
```

### Redis (Session Cache)

```typescript
// Using Redis for temporary session storage
import { createClient } from 'redis';

const redis = createClient({ url: process.env.REDIS_URL });

export async function cacheThread(threadId: string, messages: any[]) {
  await redis.setEx(
    `thread:${threadId}`,
    3600, // 1 hour TTL
    JSON.stringify(messages)
  );
}

export async function getCachedThread(threadId: string) {
  const cached = await redis.get(`thread:${threadId}`);
  return cached ? JSON.parse(cached) : null;
}
```

## Troubleshooting

### Messages Not Persisting

**Problem**: Messages aren't saved to Firestore

**Solutions**:
1. Check Firebase configuration
2. Verify Firestore rules allow writes
3. Ensure `addMessages()` is called after streaming completes
4. Check for errors in browser/server console

### Slow Query Performance

**Problem**: Loading threads/messages is slow

**Solutions**:
1. Add Firestore indexes for common queries
2. Implement pagination
3. Cache frequently accessed data
4. Use composite indexes for complex queries

### Thread List Not Updating

**Problem**: New threads don't appear in the list

**Solutions**:
1. Refresh thread list after creation
2. Use real-time listeners for automatic updates
3. Check that `updatedAt` timestamp is being set

## Next Steps

- Implement real-time updates with Firestore listeners
- Add message search functionality
- Implement conversation export/import
- Add conversation sharing features
- Implement conversation analytics

## Resources

- **Firebase Documentation**: [https://firebase.google.com/docs/firestore](https://firebase.google.com/docs/firestore)
- **Thesys C1 Docs**: [https://docs.thesys.dev](https://docs.thesys.dev)
- **Official Guide**: [https://docs.thesys.dev/guides/conversational/persistence](https://docs.thesys.dev/guides/conversational/persistence)
