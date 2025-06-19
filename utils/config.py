import os
from datetime import datetime

import yaml


class mainConfig:
    """
    Class to manage the main configuration for the application.
    Handles reading, writing, and updating configuration files in YAML format.
    """

    def __init__(self):
        """
        Initializes the configuration with default values.
        """
        self.config = {
            "screen": {
                "x_grid_max": 64,
                "y_grid_max": 32,
                "square_tam": 10,
                "space_tam": 2,
            },
            "game": {"characters_num": 4},
        }

    def read_config(self):
        """
        Reads the configuration from 'config/config.yaml' if it exists.
        If the file does not exist, creates the directory and file with default values.
        """
        if not os.path.exists("config"):
            os.makedirs("config")  # Create config directory if it doesn't exist
        if os.path.isfile("config/config.yaml"):
            with open("config/config.yaml") as yfile:
                # Load YAML configuration file
                data = yaml.load(yfile, Loader=yaml.loader.SafeLoader)
            self.config = data
        else:
            print("No config file. Loading default.")
            # Write default configuration to file
            with open("config/config.yaml", "w") as yfile:
                yaml.dump(self.config, yfile)

    def update_config(self):
        """
        Updates the configuration file.
        Backs up the current config file with a timestamp before writing the new configuration.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        os.rename("config/config.yaml", "config/config_%s.yaml" % timestamp)
        with open("config/config.yaml", "w") as yfile:
            yaml.dump(self.config, yfile)


if __name__ == "__main__":
    # Example usage: create config object and read configuration
    a = mainConfig()
    a.read_config()
