-- Teachers table
CREATE TABLE teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canvas_user_id TEXT UNIQUE NOT NULL,
    canvas_access_token TEXT,
    name TEXT,
    email TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Threads table
CREATE TABLE threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    external_id TEXT, -- For client-side message IDs
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Courses cache table
CREATE TABLE courses_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    canvas_course_id TEXT NOT NULL,
    course_data JSONB NOT NULL,
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(teacher_id, canvas_course_id)
);

-- Indexes
CREATE INDEX idx_messages_thread_id ON messages(thread_id);
CREATE INDEX idx_threads_teacher_id ON threads(teacher_id);
CREATE INDEX idx_courses_cache_teacher_id ON courses_cache(teacher_id);
