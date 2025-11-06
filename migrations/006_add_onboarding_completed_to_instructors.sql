-- Add onboarding_completed flag to instructors table
ALTER TABLE instructors
ADD COLUMN onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE;

-- Add comment to document the column
COMMENT ON COLUMN instructors.onboarding_completed IS 'Indicates whether the instructor has completed the onboarding process';
