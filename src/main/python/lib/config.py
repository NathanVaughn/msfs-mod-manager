import configparser
import functools
import os

from loguru import logger

BASE_FOLDER = os.path.abspath(os.path.join(os.getenv("APPDATA"), "MSFS Mod Manager"))
DEBUG_LOG = os.path.join(BASE_FOLDER, "debug.log")

CONFIG_FILE = os.path.abspath(os.path.join(BASE_FOLDER, "config.ini"))
SECTION_KEY = "settings"

SIM_FOLDER_KEY = "sim_folder"
# this key is kept as-is for legacy purposes
MOD_INSTALL_FOLDER_KEY = "mod_cache_folder"
LAST_OPEN_FOLDER_KEY = "last_open_folder"

LAST_VER_CHECK_KEY = "last_version_check"
NEVER_VER_CHEK_KEY = "never_version_check"

THEME_KEY = "theme"


@functools.lru_cache()
def get_key_value(key, default=None, path=False):
    """Attempts to load value from key in the config file.
    Returns a tuple of if the value was found, and if so, what the contents where."""
    logger.debug(
        "Attempting to read key '{}' from the main config file {}".format(
            key, CONFIG_FILE
        )
    )

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    # this is tiered as such, so that one missing piece doesn't cause an error
    if SECTION_KEY in config:
        logger.debug("Section key '{}' found in config file".format(SECTION_KEY))
        if key in config[SECTION_KEY]:
            value = config[SECTION_KEY][key]
            if path:
                value = os.path.normpath(value)

            logger.debug("Key '{}' found in section".format(key))
            logger.debug("Key '{}' value: {}".format(key, value))

            return (True, value)

    logger.debug("Unable to find key '{}' in config file".format(key))
    return (False, default)


def set_key_value(key, value, path=False):
    """Writes a key and value to the config file."""
    value = str(value)

    logger.debug(
        "Attempting to write key '{}' and value '{}' to the main config file {}".format(
            key, value, CONFIG_FILE
        )
    )

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    if SECTION_KEY not in config:
        logger.debug(
            "Section key '{}' not found in config file, adding it".format(SECTION_KEY)
        )
        config.add_section(SECTION_KEY)

    # if it's a path. normalize it
    if path:
        value = os.path.normpath(value)
    config[SECTION_KEY][key] = value

    logger.debug("Writing out config file")
    with open(CONFIG_FILE, "w") as f:
        config.write(f)

    # clear the cache
    get_key_value.cache_clear()
