import lib.config as config

FS_THEME = "fs"


def get_theme():
    """Returns True if FS theme is selected, otherwise returns False"""
    succeed, value = config.get_key_value(config.THEME_KEY)
    return succeed and value == FS_THEME


def set_theme(appctxt, fs_theme):
    """Writes theme selection to config file and sets the app stylesheet"""
    if fs_theme:
        config.set_key_value(config.THEME_KEY, FS_THEME)
        # apply stylesheet
        stylesheet = appctxt.get_resource("fs_style.qss")
        appctxt.app.setStyleSheet(open(stylesheet, "r").read())
    else:
        config.set_key_value(config.THEME_KEY, "None")
        appctxt.app.setStyleSheet("")

