import configparser
import os

BASE_FOLDER = os.path.abspath(os.path.join(os.getenv("APPDATA"), "MSFS Mod Manager"))

CONFIG_FILE = os.path.abspath(os.path.join(BASE_FOLDER, "config.ini"))
SECTION_KEY = "settings"
SIM_PATH_KEY = "sim_path"
LAST_VER_CHECK_KEY = "last_version_check"
THEME_KEY = "theme"

def get_key_value(key):
    """Attempts to load value from key in the config file.
    Returns a tuple of if the value was found, and if so, what the contents where"""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    # this is tiered as such, so that one missing piece doesn't cause an error
    if SECTION_KEY in config:
        if key in config[SECTION_KEY]:
            return (True, config[SECTION_KEY][key])

    return (False, None)

def set_key_value(key, value):
    """Writes a key and value to the config file"""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    if SECTION_KEY not in config:
        config.add_section(SECTION_KEY)

    config[SECTION_KEY][key] = value

    with open(CONFIG_FILE, "w") as f:
        config.write(f)
