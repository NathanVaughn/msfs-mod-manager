import lib.config as config
from loguru import logger

FS_THEME = "fs"


def get_theme():
    """Returns True if FS theme is selected, otherwise returns False."""
    logger.debug("Getting application theme from config file")
    succeed, value = config.get_key_value(config.THEME_KEY)
    status = succeed and value == FS_THEME
    logger.debug("FS theme is selected: {}".format(status))
    return status


def set_theme(appctxt, fs_theme):
    """Writes theme selection to config file and sets the app stylesheet."""
    logger.debug("Writing theme selection to config file")
    if fs_theme:
        config.set_key_value(config.THEME_KEY, FS_THEME)

        # apply stylesheet
        logger.debug(
            "Applying application stylesheet {}".format(
                appctxt.get_resource("fs_style.qss")
            )
        )
        stylesheet = appctxt.get_resource("fs_style.qss")
        appctxt.app.setStyleSheet(open(stylesheet, "r").read())
    else:
        config.set_key_value(config.THEME_KEY, "None")

        logger.debug("Clearing application stylesheet")
        appctxt.app.setStyleSheet("")
