-- Threads table for conversation management
CREATE TABLE IF NOT EXISTS threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id TEXT REFERENCES teachers(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages table for conversation history
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    external_id TEXT, -- For client-side message IDs
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Courses cache table for Canvas course data
CREATE TABLE IF NOT EXISTS courses_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id TEXT REFERENCES teachers(id) ON DELETE CASCADE,
    canvas_course_id TEXT NOT NULL,
    course_data JSONB NOT NULL,
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(teacher_id, canvas_course_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_threads_teacher_id ON threads(teacher_id);
CREATE INDEX IF NOT EXISTS idx_courses_cache_teacher_id ON courses_cache(teacher_id);

-- Add canvas fields to existing teachers table if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='teachers' AND column_name='canvas_user_id') THEN
        ALTER TABLE teachers ADD COLUMN canvas_user_id TEXT UNIQUE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='teachers' AND column_name='canvas_access_token') THEN
        ALTER TABLE teachers ADD COLUMN canvas_access_token TEXT;
    END IF;
END $$;
