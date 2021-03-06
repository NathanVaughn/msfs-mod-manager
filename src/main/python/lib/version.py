import ctypes
import datetime
import json
import os
import sys
import urllib.request
from typing import Callable, Union

from fbs_runtime.application_context.PySide2 import ApplicationContext
from loguru import logger

import lib.config as config
import lib.files as files
import lib.thread as thread
import lib.type_helper as type_helpers

INSTALLER = "MSFSModManagerSetup.exe"


class download_new_version_thread(thread.base_thread):
    """Setup a thread to download the new version and not block the main thread."""

    def __init__(self, asset_url: str) -> None:
        """Initialize the version downloader thread."""
        logger.debug("Initialzing version downloader thread")
        function = lambda: download_new_version(
            asset_url, percent_func=self.percent_update.emit  # type: ignore
        )
        thread.base_thread.__init__(self, function)


def get_version(appctxt: ApplicationContext) -> str:
    """Returns the version of the application."""
    logger.debug("Attemping to determine current application version")
    try:
        logger.debug("Parsing {}".format(appctxt.get_resource("base.json")))
        with open(appctxt.get_resource("base.json"), "r") as fp:
            data = json.load(fp)
        version = "v{}".format(data["version"])
        logger.debug("Version found: {}".format(version))
        return version
    except Exception:
        logger.exception("Determining application version failed")
        return "v??"


def is_installed() -> bool:
    """Returns if application is installed version"""
    return os.path.isfile(os.path.join(os.getcwd(), "uninstall.exe"))


def check_version_config(time_format: str) -> bool:
    """Checks config file to see if update check should proceed."""
    # first try to check if updates are supressed
    logger.debug("Trying to read never version check from config file")
    succeed, value = config.get_key_value(config.NEVER_VER_CHEK_KEY)
    if succeed and type_helpers.str2bool(value):
        return False

    # first try to read from the config file
    logger.debug("Trying to read last version check from config file")
    succeed, value = config.get_key_value(config.LAST_VER_CHECK_KEY)
    if not succeed:
        logger.debug("Unable to read last version check from config file")
        return True

    try:
        # check if last successful version check was less than a day ago.
        # If so, skip
        logger.debug("Trying to parse value {} to datetime".format(value))
        last_check = datetime.datetime.strptime(value, time_format)
        now = datetime.datetime.now()

        if last_check > (now - datetime.timedelta(days=1)):
            logger.debug(
                "Current time {} is less than one day from last check {}".format(
                    now, value
                )
            )
            return False
        else:
            logger.debug(
                "Current time {} is more than one day from last check {}".format(
                    now, value
                )
            )
    except ValueError:
        logger.exception("Parsing {} to datetime failed".format(value))

    return True


def check_version(
    appctxt: ApplicationContext, installed: bool = False
) -> Union[bool, str]:
    """Returns the release URL if a new version is installed.
    Otherwise, returns False."""
    logger.debug("Checking if a new version is available")
    time_format = "%Y-%m-%d %H:%M:%S"

    if not check_version_config(time_format):
        return False

    # open the remote url
    url = "https://api.github.com/repos/NathanVaughn/msfs-mod-manager/releases/latest"

    try:
        logger.debug("Attempting to open url {}".format(url))
        # always will be opening the above hard-coded URL
        page = urllib.request.urlopen(url)  # nosec
    except Exception:
        logger.exception("Opening url {} failed".format(url))
        return False

    # read page contents
    logger.debug("Reading page contents")
    data = page.read()
    data = data.decode("utf-8")

    # parse the json
    try:
        logger.debug("Attemping to parse page contents")
        parsed_data = json.loads(data)
        remote_version = parsed_data["tag_name"]

        if parsed_data["prerelease"]:
            return False
    except Exception:
        logger.exception("Parsing page contents failed")
        return False

    logger.debug("Remote version found is: {}".format(remote_version))

    # write the config file back out
    logger.debug("Writing out last version check time to config file")
    config.set_key_value(
        config.LAST_VER_CHECK_KEY,
        datetime.datetime.strftime(datetime.datetime.now(), time_format),
    )

    # check if remote version is newer than local version
    if not (remote_version > get_version(appctxt)):
        logger.debug("Remote version is not newer than local version")
        return False

    # if so, return release url
    logger.debug("Remote version is newer than local version")
    download_url = False

    if installed:
        # return setup.exe url
        for asset in parsed_data["assets"]:
            if asset["name"].endswith(".exe"):
                download_url = asset["browser_download_url"]
                break
    else:
        # return release url
        download_url = parsed_data["html_url"]

    logger.debug("New release url: {}".format(download_url))
    return download_url


def download_new_version(
    asset_url: str, percent_func: Callable = None
) -> Union[str, bool]:
    """Downloads new installer version. Returns False if download failed."""
    download_path = os.path.join(os.path.expanduser("~"), "Downloads", INSTALLER)

    # delete existing installer if it exists
    files.delete_file(download_path)

    def request_hook(block_num: int, block_size: int, total_size: int) -> None:
        if total_size > 0:
            readsofar = block_num * block_size
            percent = readsofar * 100 / total_size
            percent_func(percent)

    # download file
    try:
        logger.debug("Attempting to download url {}".format(asset_url))
        if percent_func:
            # this update function is for a percentage
            urllib.request.urlretrieve(asset_url, download_path, request_hook)  # nosec
        else:
            urllib.request.urlretrieve(asset_url, download_path)  # nosec
    except Exception:
        logger.exception("Downloading url {} failed".format(asset_url))
        return False

    logger.debug("Download succeeded")
    return download_path


def install_new_version(installer_path: str) -> None:
    """Runs the new installer and causes a UAC prompt."""
    # https://docs.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shellexecutew
    logger.debug("ShellExecuteW {}".format(installer_path))
    ctypes.windll.shell32.ShellExecuteW(None, "runas", installer_path, "", None, 1)

    # https://stackoverflow.com/questions/2129935/pyinstaller-exes-not-dying-after-sys-exit
    logger.debug("Exiting")
    sys.exit()

    # insurance if above fails
    logger.debug("REALLY exiting")
    os._exit(0)
