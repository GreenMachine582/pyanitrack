
import argparse
import logging
from os import path as os_path

from src import pyanitrack

_logger = logging.getLogger(__name__)

MODULE_DIR = os_path.dirname(os_path.abspath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument("--instance", default="", help="instance name will be used to locate config (default: '')")
parser.add_argument("--config_path", default="", help="path to desired config (default: '')")
parser.add_argument("--logs_dir", default="", help="directory to desired logs (default: '')")


def upgradeDB(env, from_version: int, to_version: int):
    """ Upgrade the database from schema v1 to v2. """
    try:
        # Ensure the database connection is available
        conn, cur = pyanitrack.database.connect(env)

        # Check if the current database schema version matches the target version
        db_version = pyanitrack.database.getSchemaVersion(cur)
        if db_version != from_version:
            raise Exception(f"DB version is {db_version}, however the target version is {from_version}.")

        pyanitrack.database.upgradeDatabase(env, from_version, to_version)
        _logger.info(f"Database has been populated and transformed to v{to_version}.")

    except Exception as e:
        _logger.error(f"An error occurred while upgrading DB: {e}")


def main():
    """
    Main function to load the environment, parse command-line arguments, and execute the data loading process.
    """
    args = parser.parse_args()
    instance: str = args.instance
    config_path: str = args.config_path
    logs_dir: str = args.logs_dir

    project_name = pyanitrack.version.PROJECT_NAME

    # Determine default config and logs paths if not provided
    if not config_path:
        config_filename = f"{project_name}{'' if not instance else '_' + instance}.conf"
        config_path = f"configs/{config_filename}"
    if not logs_dir:
        logs_instance_folder = f"{project_name}{'' if not instance else '_' + instance}"
        logs_dir = f"logs/{logs_instance_folder}"

    config_path = os_path.abspath(config_path)
    logs_dir = os_path.abspath(logs_dir)

    # Load environment and configurations
    env = pyanitrack.loadEnv(config_path, project_dir=MODULE_DIR, instance=instance, logs_dir=logs_dir)
    _logger.info(f"Starting {env.project_name_text}.")

    upgradeDB(env, 1, 2)


if __name__ == "__main__":
    main()