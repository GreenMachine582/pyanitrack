
import argparse
import logging
from os import path as os_path

import pandas as pd

from src import pyanitrack

_logger = logging.getLogger(__name__)

MODULE_DIR = os_path.dirname(os_path.abspath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument("--instance", default="", help="instance name will be used to locate config (default: '')")
parser.add_argument("--config_path", default="", help="path to desired config (default: '')")
parser.add_argument("--logs_dir", default="", help="directory to desired logs (default: '')")


def loadDataFromExcel(env, excel_file_path: str, target_version: int):
    """Load data from an Excel file and insert it into the database with transaction rollback on error."""
    conn, cur = None, None
    try:
        # Ensure the database connection is available
        try:
            conn, cur = pyanitrack.database.connect(env, autocommit=False)
        except pyanitrack.DatabaseNotFoundError:
            pyanitrack.database.createDatabase(env, target_version)
            conn, cur = pyanitrack.database.connect(env, autocommit=False)

        # Check if the current database schema version matches the target version
        db_version = pyanitrack.database.getSchemaVersion(cur)
        if db_version != target_version:
            raise Exception(f"DB version is {db_version}, however the target version is {target_version}.")

        # Load the Excel file, ensuring all data is read as strings
        df = pd.read_excel(excel_file_path, usecols="A:G", dtype=str, engine='openpyxl')
        # Replace NaN values with empty strings in the 'Genres' column
        df['Genres'] = df['Genres'].fillna('')

        _logger.info("Excel file loaded successfully.")

        # Loop through each row in the DataFrame and insert the data into the database
        for index, row in df.iterrows():
            name = row.iloc[0]
            season = int(row.iloc[1])
            episode = int(row.iloc[2])
            times_watched = int(row.iloc[3])
            streaming_service = row.iloc[4]
            watch_date = row.iloc[5]
            genres = row.iloc[6]

            # Insert the row into the anime table
            cur.execute("""
                INSERT INTO anime (name, season, episode, times_watched, service, watch_date, genres)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, season, episode, times_watched, streaming_service, watch_date, genres))

        # Commit the transaction after all rows are inserted
        conn.commit()
        _logger.info(f"Data from Excel has been successfully loaded into the database v{target_version}.")

    except Exception as e:
        _logger.error(f"An error occurred while loading data from Excel: {e}")
        if conn:
            _logger.debug("Rolling back the transaction due to error.")
            conn.rollback()  # Rollback the transaction if any error occurs
        raise
    finally:
        if conn:
            conn.close()  # Ensure the connection is closed
            _logger.debug("Database connection closed.")



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

    # Load data from Excel into the version 1 database
    excel_file_path = os_path.abspath(f"cache/Culture Records.xlsx")
    loadDataFromExcel(env, excel_file_path, 1)


if __name__ == "__main__":
    main()