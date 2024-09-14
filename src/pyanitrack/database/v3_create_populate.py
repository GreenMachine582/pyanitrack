import logging

from . import v2_create_populate

_logger = logging.getLogger(__name__)


def populateLookupTables(env):
    """ Populate lookup tables with initial data. """
    v2_create_populate.populateLookupTables(env)

    # Content Statuses Table
    content_statuses = ['Completed', 'Dropped', 'Queue']
    for status in content_statuses:
        env.cur.execute("INSERT INTO content_status (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (status,))


def populate(env):
    """ Populate the database with initial data. """
    _logger.info("Populating the database lookup tables with initial data...")
    populateLookupTables(env)

    # _logger.info("Starting data transformation for anime table...")
    _logger.info("Initial data population completed.")
