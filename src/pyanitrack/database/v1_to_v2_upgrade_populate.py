import logging

_logger = logging.getLogger(__name__)

def populate(env):
    """ Data transformation from v1 to v2. """
    _logger.info("Populating the database with initial data.")

    # Genres Table
    genres = ['Action', 'Adventure', 'Comedy', 'Drama', 'Ecchi', 'Fan Service', 'Fantasy', 'Gore', 'Harem',
              'Historical', 'Horror', 'Isekai', 'Magic', 'Martial Arts', 'Mecha', 'Methodology', 'Mystery',
              'Psychological', 'Reincarnation', 'Romance', 'School', 'Sci-Fi', 'Shonen', 'Slice of Life',
              'Supernatural', 'Super Power', 'Suspense', 'Survival']
    for genre in genres:
        env.cur.execute("INSERT INTO genre (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (genre,))

    # Stream Services Table
    stream_services = [
        ('AnimeLab', 'https://www.animelab.com'),
        ('Crunchyroll', 'https://www.crunchyroll.com'),
        ('Funimation', 'https://www.funimation.com'),
        ('HiDive', 'https://www.hidive.com'),
        ('Netflix', 'https://www.netflix.com')
    ]

    for stream_service in stream_services:
        env.cur.execute(
            "INSERT INTO stream_service (name, domain_url) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING;",
            stream_service
        )

    # Anime Statuses Table
    anime_statuses = ['Watching', 'Completed', 'On Hold', 'Dropped', 'Queue']
    for status in anime_statuses:
        env.cur.execute("INSERT INTO anime_status (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (status,))

    _logger.info("Starting data transformation for anime table...")

    # Migrate data from anime_old to anime
    env.cur.execute("""
            INSERT INTO anime (name, display_name, summary, url, service, thumbnail_url)
            SELECT name, name AS display_name, 'No summary available' AS summary, NULL AS url, service, NULL AS thumbnail_url
            FROM anime_old
        """)
    _logger.info("Data migrated successfully from anime_old to anime.")

    # Drop the old anime table
    env.cur.execute("DROP TABLE IF EXISTS anime_old")
    _logger.info("Old anime table dropped successfully.")
