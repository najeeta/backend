-- Migration: Rename teachers to instructors throughout the database
-- This migration renames the teachers table and all related foreign key columns and indexes

-- Step 1: Rename the main table
ALTER TABLE teachers RENAME TO instructors;

-- Step 2: Rename the index on instructors table
ALTER INDEX idx_teachers_clerk_user_id RENAME TO idx_instructors_clerk_user_id;

-- Step 3: Rename teacher_id column in threads table
ALTER TABLE threads RENAME COLUMN teacher_id TO instructor_id;

-- Step 4: Rename the index on threads.instructor_id
ALTER INDEX idx_threads_teacher_id RENAME TO idx_threads_instructor_id;

-- Step 5: Rename teacher_id column in courses_cache table (if it exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name='courses_cache' AND column_name='teacher_id') THEN
        ALTER TABLE courses_cache RENAME COLUMN teacher_id TO instructor_id;
    END IF;
END $$;

-- Step 6: Rename the index on courses_cache.instructor_id (if it exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_courses_cache_teacher_id') THEN
        ALTER INDEX idx_courses_cache_teacher_id RENAME TO idx_courses_cache_instructor_id;
    END IF;
END $$;

-- Note: Foreign key constraints automatically update to reference the renamed table and columns
-- PostgreSQL handles this automatically when you rename tables/columns that are part of FK relationships
