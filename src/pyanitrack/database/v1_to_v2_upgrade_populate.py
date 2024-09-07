import logging

_logger = logging.getLogger(__name__)

def populate(env):
    """ Data transformation from v1 to v2. """
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
