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

        -- Genres Table
        CREATE TABLE genre (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL
        );

        -- Stream Services Table
        CREATE TABLE stream_service (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            domain_url VARCHAR(255)
        );

        -- Create new anime table with updated structure
        CREATE TABLE anime (
            id SERIAL PRIMARY KEY,
            name VARCHAR(150) UNIQUE NOT NULL,
            display_name VARCHAR(150) NOT NULL
        );

        -- Seasons Table
        CREATE TABLE season (
            id SERIAL PRIMARY KEY,
            number INTEGER NOT NULL,
            anime INTEGER REFERENCES anime(id) ON DELETE CASCADE,
            episode_count INTEGER NOT NULL,
            myanimelist_url VARCHAR(255),
            mal_id INTEGER NOT NULL,
            thumbnail_url VARCHAR(255),
            ep_duration INTEGER NOT NULL,
            summary TEXT,
            UNIQUE (anime, number)
        );

        -- Episodes Table
        CREATE TABLE episode (
            id SERIAL PRIMARY KEY,
            season INTEGER REFERENCES season(id) ON DELETE CASCADE,
            number INTEGER NOT NULL,
            anime INTEGER REFERENCES anime(id) ON DELETE CASCADE,
            UNIQUE (season, number)
        );

        -- Watch History Table
        CREATE TABLE watch_history (
            id SERIAL PRIMARY KEY,
            anime INTEGER REFERENCES anime(id) ON DELETE CASCADE,
            season INTEGER REFERENCES season(id),
            date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            eps_watched INTEGER NOT NULL,
            completion_percentage FLOAT NOT NULL
        );

        -- Anime-Genre Join Table
        CREATE TABLE anime_genre (
            anime_id INTEGER REFERENCES anime(id) ON DELETE CASCADE,
            genre_id INTEGER REFERENCES genre(id) ON DELETE CASCADE,
            PRIMARY KEY (anime_id, genre_id)
        );

        -- Anime-Stream Service Join Table
        CREATE TABLE anime_stream_service (
            anime_id INTEGER REFERENCES anime(id) ON DELETE CASCADE,
            stream_service_id INTEGER REFERENCES stream_service(id) ON DELETE CASCADE,
            PRIMARY KEY (anime_id, stream_service_id)
        );

        -- Insert Initial Version Record
        INSERT INTO schema_version (version, description) VALUES (2, 'v1-v2: Split the anime table in relational tables');

    END IF;
END $$;
