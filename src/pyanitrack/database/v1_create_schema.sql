-- Create Schema Versioning Table
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    description TEXT
);

-- Check current schema version before applying changes
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM schema_version WHERE version = 1) THEN

        -- Anime Table
        CREATE TABLE anime (
            id SERIAL PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            season INTEGER NOT NULL,
            episode INTEGER NOT NULL,
            times_watched INTEGER NOT NULL,
            service VARCHAR(50),
            watch_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            genres VARCHAR(100) NOT NULL
        );

        -- Insert Initial Version Record
        INSERT INTO schema_version (version, description) VALUES (1, 'Initial schema creation');

    END IF;
END $$;
