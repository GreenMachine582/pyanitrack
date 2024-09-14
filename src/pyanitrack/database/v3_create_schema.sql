-- Create Schema Versioning Table
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    description TEXT
);

-- Check current schema version before applying changes
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM schema_version WHERE version = 2) THEN

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

        -- Anime Table
        CREATE TABLE anime (
            id SERIAL PRIMARY KEY,
            name VARCHAR(150) UNIQUE NOT NULL,
            display_name VARCHAR(150) NOT NULL,
            summary TEXT,
            url VARCHAR(255),
            thumbnail_url VARCHAR(255)
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
            title VARCHAR(150) NOT NULL,
            UNIQUE (season, number)
        );

        -- Users Table
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL
        );

        -- Watch History Table
        CREATE TABLE watch_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            anime INTEGER REFERENCES anime(id) ON DELETE CASCADE,
            season INTEGER REFERENCES season(id),
            date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            eps_watched INTEGER NOT NULL,
            completion_percentage FLOAT NOT NULL,
            score INTEGER CHECK (score >= 1 AND score <= 10)
        );

        -- Content Status Table
        CREATE TABLE content_status (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL
        );

        -- User Anime Status Table
        CREATE TABLE user_anime_status (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            anime INTEGER REFERENCES anime(id) ON DELETE CASCADE,
            watch_status INTEGER REFERENCES content_status(id),
            last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        -- Anime Reviews Table
        CREATE TABLE review_anime (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            anime INTEGER REFERENCES anime(id) ON DELETE CASCADE,
            review_text TEXT NOT NULL,
            date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        );

        -- Episode Reviews Table
        CREATE TABLE review_episode (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            episode INTEGER REFERENCES episode(id) ON DELETE CASCADE,
            review_text TEXT NOT NULL,
            date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            score INTEGER CHECK (score >= 1 AND score <= 10)
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
        INSERT INTO schema_version (version, description) VALUES (3, 'Initial schema creation');

    END IF;
END $$;
