
import argparse
import logging
import os

from src import pyanitrack

_logger = logging.getLogger(__name__)

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument("--instance", default="", help="instance name will be used to locate config (default: '')")
parser.add_argument("--config_path", default="", help="path to desired config (default: '')")
parser.add_argument("--logs_dir", default="", help="directory to desired logs (default: '')")


def main():
    args = parser.parse_args()
    instance: str = args.instance
    config_path: str = args.config_path
    logs_dir: str = args.logs_dir

    project_name = pyanitrack.version.PROJECT_NAME

    if not config_path:
        config_filename = f"{project_name}{'' if not instance else '_' + instance}.conf"
        config_path = f"configs/{config_filename}"
    if not logs_dir:
        logs_instance_folder = f"{project_name}{'' if not instance else '_' + instance}"
        logs_dir = f"logs/{logs_instance_folder}"

    env = pyanitrack.loadEnv(config_path, project_dir=MODULE_DIR, instance=instance, logs_dir=logs_dir)
    _logger.info(f"Starting {env.project_name_text}.")


if __name__ == "__main__":
    main()