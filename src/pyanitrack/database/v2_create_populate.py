import logging

_logger = logging.getLogger(__name__)

def populate(env):
    """ Populate the database with initial data. """
    genres = ['Adventure', 'Action', 'Comedy', 'Drama', 'Ecchi', 'Fantasy', 'Harem', 'Horror', 'Isekai', 'Magic',
              'Mecha', 'Romance', 'Sci-Fi', 'Shonen', 'Slice of Life', 'Supernatural']
    for genre in genres:
        env.cur.execute("INSERT INTO genre (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (genre,))

    anime_statuses = ['Watching', 'Completed', 'On Hold', 'Dropped', 'Queue']
    for status in anime_statuses:
        env.cur.execute("INSERT INTO anime_status (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (status,))

    _logger.info("Initial data population completed.")