import datetime
import json
import urllib.request
import datetime

from loguru import logger

import lib.config as config


def get_version(appctxt):
    """Returns the version of the application"""
    logger.debug("Attemping to determine current application version")
    try:
        logger.debug("Parsing {}".format(appctxt.get_resource("base.json")))
        with open(appctxt.get_resource("base.json"), "r") as fp:
            data = json.load(fp)
        version = "v{}".format(data["version"])
        logger.debug("Version found: {}".format(version))
        return version
    except Exception as e:
        logger.exception("Determining application version failed")
        return "v??"


def check_version(appctxt):
    """Returns the release URL if a new version is installed. Otherwise,
    returns False"""
    logger.debug("Checking if a new version is available")
    time_format = "%Y-%m-%d %H:%M:%S"

    # first try to read from the config file
    logger.debug("Trying to read last version check from config file")
    succeed, value = config.get_key_value(config.LAST_VER_CHECK_KEY)
    if succeed:
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
    else:
        logger.debug("Unable to read last version check from config file")

    # open the remote url
    url = "https://api.github.com/repos/NathanVaughn/msfs-mod-manager/releases/latest"

    try:
        logger.debug("Attempting to open url {}".format(url))
        page = urllib.request.urlopen(url)
    except Exception as e:
        logger.exception("Opening url {} failed".format(url))
        return

    # read page contents
    logger.debug("Reading page contents")
    data = page.read()
    data = data.decode("utf-8")

    # parse the json
    try:
        logger.debug("Attemping to parse page contents")
        parsed_data = json.loads(data)
        remote_version = parsed_data["tag_name"]
    except Exception as e:
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
    if remote_version > get_version(appctxt):
        # if so, return release url
        logger.debug("Remote version is newer than local version")
        return parsed_data["html_url"]
    else:
        logger.debug("Remote version is not newer than local version")
        return False
