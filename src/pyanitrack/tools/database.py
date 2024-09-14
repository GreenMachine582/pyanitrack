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


def connect(env, **kwargs):
    """ Connect to the project database server. """
    params = env.config["database"].copy()
    params.update(kwargs)
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


def getLatestAvailableVersion(database_dir: str):
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
    method = "upgrade" if from_version else "create"
    version_text = f"v{from_version} to v{to_version}" if from_version else f"v{to_version}"

    if not from_version:  # Creation case
        schema_file = os_path.join(database_dir, f"v{to_version}_create_schema.sql")
    else:  # Upgrade case
        schema_file = os_path.join(database_dir, f"v{from_version}_to_v{to_version}_upgrade_schema.sql")

    _logger.debug(f"Applying {method} schema for {version_text}...")

    try:
        with open(schema_file, 'r') as file:
            cursor.execute(file.read())
        _logger.debug(f"{method.capitalize()} schema for {version_text} applied successfully.")
    except FileNotFoundError:
        _logger.error(f"{method.capitalize()}  schema file {schema_file} not found.")
        raise SchemaFileNotFoundError(f"Schema file {schema_file} not found.")
    except (Exception, psycopg2.DatabaseError) as error:
        _logger.error(f"Error applying {method} schema for {version_text}: {error}")
        raise SchemaApplicationError(f"Error applying {method} schema for {version_text}: {error}")


def runDataPopulationScript(database_dir: str, from_version: int, to_version: int, env) -> bool:
    """Look for and run a Python script to populate or upgrade the database."""
    method = "upgrade" if from_version else "create"
    version_text = f"v{from_version} to v{to_version}" if from_version else f"v{to_version}"

    if not from_version:  # Creation case
        script_file = os_path.join(database_dir, f"v{to_version}_create_populate.py")
    else:  # Upgrade case
        script_file = os_path.join(database_dir, f"v{from_version}_to_v{to_version}_upgrade_populate.py")

    if not os_path.exists(script_file):
        _logger.debug(f"No {method} population script found for {version_text}.")
        return False

    _logger.debug(f"Starting transaction for {method} population script for {version_text}...")

    try:
        env.cur.execute("BEGIN")  # Start a transaction

        _logger.debug(f"Running data population script: {script_file}")
        script_namespace = {}
        with open(script_file, 'r') as file:
            exec(file.read(), script_namespace)
        if 'populate' in script_namespace:
            script_namespace['populate'](env)
            _logger.debug("Data population script executed successfully.")
        else:
            _logger.warning(f"No 'populate' function found in {script_file}.")

        env.cur.execute("COMMIT")  # Commit the transaction if everything goes well
        _logger.debug("Transaction committed successfully.")
        return True

    except Exception as e:
        _logger.error(f"Error during data population: {e}")
        env.cur.execute("ROLLBACK")  # Rollback the entire transaction
        raise DataPopulationError("An error occurred during data population. Transaction rolled back.")


def createDatabase(env, version: int = None):
    """Create the database from the newest or specified version with proper locking."""
    params = env.config["database"]
    db_name = params.get("dbname")
    _logger.info(f"Creating database {db_name} from v{version}...")

    database_dir = os_path.join(env.PROJECT_DIR, "database", "")
    conn = None

    try:
        # Connect to the default PostgreSQL database to create the project database
        default_params = params.copy()
        default_params['dbname'] = 'postgres'  # Use the default 'postgres' db to create the new database
        conn, cur = _connect(env, **default_params)

        # Check if the database already exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", [db_name])
        exists = cur.fetchone()
        if exists:
            _logger.debug(f"Database {db_name} already exists. Proceeding with schema creation.")
        else:
            cur.execute(f"CREATE DATABASE {db_name}")
            _logger.debug(f"Database {db_name} created successfully.")

        cur.close()
        conn.close()

        # Reconnect to the newly created database to apply the schema
        params['dbname'] = db_name
        conn, cur = _connect(env, autocommit=False, **params)

        if version is None:
            version = getLatestAvailableVersion(database_dir)

        # Apply the schema for the specified version
        applySchemaVersion(database_dir, cur, 0, version)

        # Start a transaction and acquire an exclusive lock on the schema_version table
        cur.execute("BEGIN")
        cur.execute("LOCK TABLE schema_version IN ACCESS EXCLUSIVE MODE")
        _logger.debug("Acquired exclusive lock on schema_version table.")

        # Run data population script if available
        script_applied = runDataPopulationScript(database_dir, 0, version, env)

        # Commit the transaction
        conn.commit()
        _logger.info(f"Database {db_name} created{', schema and population script' if script_applied else ' and schema'} v{version} applied.")
        _logger.debug("Transaction committed successfully.")

    except DatabaseError as db_error:
        _logger.error(f"Database creation failed: {db_error}")
        if conn:
            conn.rollback()  # Rollback if an error occurs
            _logger.debug("Transaction rolled back due to error.")
        raise
    except (Exception, psycopg2.DatabaseError) as error:
        _logger.error(f"Error: {error}")
        if conn:
            conn.rollback()  # Rollback on generic error
        raise DatabaseError(f"An error occurred: {error}")
    finally:
        if conn is not None:
            conn.close()  # Close the connection
            _logger.debug(f"Database connection closed.")


def upgradeDatabase(env, from_version: int, to_version: int):
    """Upgrade the database schema from a specific version to a target version with proper locking."""
    params = env.config["database"]
    db_name = params.get("dbname")
    _logger.info(f"Upgrading database {db_name} from version {from_version} to {to_version}...")

    database_dir = os_path.join(env.PROJECT_DIR, "database", "")
    conn, cur = None, None

    try:
        # Connect to the database to apply upgrades
        conn, cur = _connect(env, autocommit=False, **params)

        # Start a transaction and acquire an exclusive lock on the schema_version table
        cur.execute("BEGIN")
        cur.execute("LOCK TABLE schema_version IN ACCESS EXCLUSIVE MODE")
        _logger.debug("Acquired exclusive lock on schema_version table.")

        # Apply schema updates from the current version to the target version
        for version in range(from_version, to_version):
            _logger.debug(f"Applying schema update for version {version}...")
            # Apply schema update
            applySchemaVersion(database_dir, cur, version, version + 1)

            # Run data population script if available
            runDataPopulationScript(database_dir, version, version + 1, env)

        # Update schema_version table with the new version
        cur.execute("""
            INSERT INTO schema_version (version, description) 
            VALUES (%s, %s) 
            ON CONFLICT (version) DO NOTHING
            """, (to_version, f'Upgraded to schema version {to_version}')
        )

        # Commit the transaction
        conn.commit()
        _logger.info(f"Database upgraded to schema version {to_version}.")
        _logger.debug("Transaction committed successfully.")

    except Exception as e:
        _logger.error(f"Error during database upgrade: {e}")
        if conn and cur:
            conn.rollback()  # Rollback the transaction on error
            _logger.debug("Transaction rolled back due to error.")
        raise DatabaseError("An error occurred during database upgrade. Transaction rolled back.")
    finally:
        if conn is not None:
            conn.close()  # Ensure the connection is closed
            _logger.debug("Database connection closed.")


def getSchemaVersion(cur):
    """Fetch the current database schema version."""
    try:
        # Query the latest version from the schema_version table
        cur.execute("""
            SELECT version
            FROM schema_version
            ORDER BY applied_at DESC
            LIMIT 1;
        """)

        # Fetch the result
        version_record = cur.fetchone()

        if version_record is None:
            # If no version is found, the database is un-versioned
            _logger.warning("No version record found. The database might not be initialised.")
            return None
        return version_record[0]
    except Exception as e:
        _logger.error(f"Error while fetching the database version: {e}")
        raise DatabaseError("Failed to get database version.")
