-- Instructors table for storing instructor information
CREATE TABLE IF NOT EXISTS instructors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_user_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for performance on clerk_user_id lookups
CREATE INDEX IF NOT EXISTS idx_instructors_clerk_user_id ON instructors(clerk_user_id);
