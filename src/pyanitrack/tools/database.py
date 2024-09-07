import logging
import os
import re
from os import path as os_path

import psycopg2
from psycopg2 import sql

_logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base class for other database-related exceptions."""
    pass

class DatabaseNotFoundError(DatabaseError):
    """Raised when the database does not exist."""
    pass

class SchemaFileNotFoundError(DatabaseError):
    """Raised when the schema file is not found."""
    pass

class SchemaApplicationError(DatabaseError):
    """Raised when an error occurs while applying the schema."""
    pass

class DataPopulationError(DatabaseError):
    """Raised when an error occurs while populating data."""
    pass


def _connect(env=None, autocommit: bool = True, **params):
    """ Establish a connection to the PostgreSQL database and return the connection and cursor objects. """
    conn = psycopg2.connect(**params)
    conn.autocommit = autocommit
    cur = conn.cursor()
    if env is not None:
        env.conn = conn
        env.cur = cur
    return conn, cur


def connect(env):
    """ Connect to the project database server. """
    params = env.config["database"]
    _logger.info(f"Connecting to the {env.project_name_text} database...")

    try:
        return _connect(env, **params)
    except psycopg2.OperationalError as db_error:
        if f'database "{params.get("dbname")}" does not exist' in db_error.args[0]:
            _logger.error(f"Database does not exist or is inaccessible: {db_error}")
            raise DatabaseNotFoundError("Database does not exist. Please create the database before proceeding.")
        raise DatabaseError(f"Operational error occurred: {db_error}")
    except (Exception, psycopg2.DatabaseError) as error:
        _logger.error(f"Error: {error}")
        raise DatabaseError(f"An error occurred: {error}")


def getLatestVersion(database_dir: str):
    """ Get the latest version of the schema. """
    files = os.listdir(database_dir)

    # Extract version numbers from filenames
    versions = []
    for f in files:
        match = re.match(r'v(\d+)_create_schema\.sql', f)
        if match:
            versions.append(int(match.group(1)))

    if not versions:
        raise ValueError("No valid schema files found.")
    return max(versions)


def applySchemaVersion(database_dir: str, cursor, from_version: int, to_version: int):
    """Apply the schema for the specified version, handling both create and upgrade scenarios."""
    if not from_version:  # Creation case
        schema_file = os_path.join(database_dir, f"v{to_version}_create_schema.sql")
    else:  # Upgrade case
        schema_file = os_path.join(database_dir, f"v{from_version}_to_v{to_version}_upgrade_schema.sql")

    _logger.info(f"Applying schema from version {from_version or 'initial'} to {to_version}...")

    try:
        with open(schema_file, 'r') as file:
            cursor.execute(file.read())
        _logger.info(f"Schema upgrade to version {to_version} applied successfully.")
    except FileNotFoundError:
        _logger.error(f"Schema file {schema_file} not found.")
        raise SchemaFileNotFoundError(f"Schema file {schema_file} not found.")
    except (Exception, psycopg2.DatabaseError) as error:
        _logger.error(f"Error applying schema version {to_version}: {error}")
        raise SchemaApplicationError(f"Error applying schema version {to_version}: {error}")


def runDataPopulationScript(database_dir: str, from_version: int, to_version: int, env):
    """Look for and run a Python script to populate or upgrade the database."""
    if not from_version:  # Creation case
        script_file = os_path.join(database_dir, f"v{to_version}_create_populate.py")
    else:  # Upgrade case
        script_file = os_path.join(database_dir, f"v{from_version}_to_v{to_version}_upgrade_population.py")

    try:
        _logger.info(f"Starting transaction for data population script from version {from_version or 'initial'} to {to_version}...")
        env.cur.execute("BEGIN")  # Start a transaction

        if os_path.exists(script_file):
            _logger.info(f"Running data population script: {script_file}")
            script_namespace = {}
            with open(script_file, 'r') as file:
                exec(file.read(), script_namespace)
            if 'populate' in script_namespace:
                script_namespace['populate'](env)
                _logger.info("Data population script executed successfully.")
            else:
                _logger.warning(f"No 'populate' function found in {script_file}.")
        else:
            _logger.info(f"No data population script found for version {to_version}.")

        env.cur.execute("COMMIT")  # Commit the transaction if everything goes well
        _logger.info("Transaction committed successfully.")

    except Exception as e:
        _logger.error(f"Error during data population: {e}")
        env.cur.execute("ROLLBACK")  # Rollback the entire transaction
        raise DataPopulationError("An error occurred during data population. Transaction rolled back.")


def createDatabase(env, version: int = None):
    """ Create the database from the newest or specified version. """
    params = env.config["database"]
    db_name = params.get("dbname")
    _logger.info(f"Creating database {db_name} from version {version}...")

    database_dir = os_path.join(env.PROJECT_DIR, "database", "")

    conn = None
    try:
        # Connect to the default database to create the project database
        default_params = params.copy()
        default_params['dbname'] = 'postgres'  # Connect to the default postgres db to execute create db
        conn, cur = _connect(env, **default_params)

        # Check if the database already exists
        cur.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [db_name])
        exists = cur.fetchone()
        if exists:
            _logger.info(f"Database {db_name} already exists. Proceeding with schema creation.")
        else:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            _logger.info(f"Database {db_name} created successfully.")

        cur.close()
        conn.close()

        # Reconnect to the newly created database to apply the schema
        params['dbname'] = db_name
        conn, cur = _connect(env, **params)

        if version is None:
            version = getLatestVersion(database_dir)

        # Apply the schema for the specified version
        applySchemaVersion(database_dir, cur, 0, version)

        # Run data population script if available
        runDataPopulationScript(database_dir, 0, version, env)

        _logger.info(f"Database {db_name} created and schema version {version} applied.")

    except DatabaseError as db_error:
        _logger.error(f"Database creation failed: {db_error}")
        raise
    except (Exception, psycopg2.DatabaseError) as error:
        _logger.error(f"Error: {error}")
        raise DatabaseError(f"An error occurred: {error}")
    finally:
        if conn is not None:
            conn.close()
            _logger.info(f"Database connection closed.")


def upgradeDatabase(env, from_version: int, to_version: int):
    """ Upgrade the database schema from a specific version to a target version. """
    params = env.config["database"]
    db_name = params.get("dbname")
    _logger.info(f"Upgrading database {db_name} from version {from_version} to {to_version}...")

    database_dir = os_path.join(env.PROJECT_DIR, "database", "")
    conn, cur = None, None

    try:
        # Connect to the database to apply upgrades
        conn, cur = _connect(env, **params)

        # Apply schema updates from the current version to the target version
        for version in range(from_version, to_version):
            _logger.info(f"Applying schema update for version {version}...")
            # Apply schema update
            applySchemaVersion(database_dir, cur, version, version + 1)

            # Run data population script if available
            runDataPopulationScript(database_dir, version, version + 1, env)

        # Update schema_version table with the new version
        cur.execute("INSERT INTO schema_version (version, description) VALUES (%s, %s) ON CONFLICT (version) DO NOTHING",
                    (to_version, f'Upgraded to schema version {to_version}'))
        _logger.info(f"Database upgraded to schema version {to_version}.")

        cur.execute("COMMIT")  # Commit the transaction if everything goes well
        _logger.info("Transaction committed successfully.")

    except Exception as e:
        _logger.error(f"Error during database upgrade: {e}")
        if conn and cur:
            cur.execute("ROLLBACK")  # Rollback the entire transaction
        raise DatabaseError("An error occurred during database upgrade. Transaction rolled back.")
    finally:
        if conn is not None:
            conn.close()
            _logger.info("Database connection closed.")

