import logging

_logger = logging.getLogger(__name__)


def populateLookupTables(env):
    """ Populate lookup tables with initial data. """
    # Genres Table
    genres = ['Action', 'Adventure', 'Comedy', 'Drama', 'Ecchi', 'Fan Service', 'Fantasy', 'Harem', 'Historical',
              'Horror', 'Isekai', 'Magic', 'Martial Arts', 'Mecha', 'Mystery', 'Romance', 'School', 'Sci-Fi', 'Shonen',
              'Slice of Life', 'Supernatural']
    for genre in genres:
        env.cur.execute("INSERT INTO genre (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (genre,))

    # Stream Services Table
    stream_services = [
        ('AnimeLab', 'https://www.animelab.com'),
        ('Crunchyroll', 'https://www.crunchyroll.com'),
        ('Funimation', 'https://www.funimation.com'),
        ('HiDive', 'https://www.hidive.com'),
        ('Netflix', 'https://www.netflix.com'),
        ('Other', None)
    ]

    for stream_service in stream_services:
        env.cur.execute(
            "INSERT INTO stream_service (name, domain_url) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING;",
            stream_service
        )


def populate(env):
    """ Populate the database with initial data. """
    _logger.info("Populating the database lookup tables with initial data...")
    populateLookupTables(env)

    _logger.info("Initial data population completed.")