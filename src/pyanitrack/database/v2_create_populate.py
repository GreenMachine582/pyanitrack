import logging

_logger = logging.getLogger(__name__)

def populate(env):
    """ Populate the database with initial data. """
    # Genres Table
    genres = ['Adventure', 'Action', 'Comedy', 'Drama', 'Ecchi', 'Fantasy', 'Harem', 'Horror', 'Isekai', 'Magic',
              'Mecha', 'Romance', 'Sci-Fi', 'Shonen', 'Slice of Life', 'Supernatural']
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

    # Anime Statuses Table
    anime_statuses = ['Watching', 'Completed', 'On Hold', 'Dropped', 'Queue']
    for status in anime_statuses:
        env.cur.execute("INSERT INTO anime_status (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (status,))

    _logger.info("Initial data population completed.")