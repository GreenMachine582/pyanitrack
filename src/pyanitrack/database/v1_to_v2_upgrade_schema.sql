-- Create Schema Versioning Table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    description TEXT
);

-- Check current schema version before applying changes
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM schema_version WHERE version = 2) THEN

        -- Rename old anime table for backup
        ALTER TABLE anime RENAME TO anime_old;

        -- Create new anime table with updated structure
        CREATE TABLE anime (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            display_name VARCHAR(100) NOT NULL,
            summary TEXT,
            url VARCHAR(255),
            service VARCHAR(50),
            thumbnail_url VARCHAR(255)
        );

        -- Insert Initial Version Record
        INSERT INTO schema_version (version, description) VALUES (2, 'Updated anime table structure');

    END IF;
END $$;
