-- Migration: Rename teacher_id to instructor_id in classes and lms_connections tables
-- This completes the teacher -> instructor refactoring across all tables

-- Step 1: Rename teacher_id column in classes table
ALTER TABLE classes RENAME COLUMN teacher_id TO instructor_id;

-- Step 2: Rename teacher_id column in lms_connections table
ALTER TABLE lms_connections RENAME COLUMN teacher_id TO instructor_id;

-- Note: PostgreSQL automatically updates foreign key constraints and indexes
-- when columns are renamed, so no additional steps are needed
