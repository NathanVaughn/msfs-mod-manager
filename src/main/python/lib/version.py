import configparser
import datetime
import json
import urllib.request

from lib.flight_sim import CONFIG_FILE, LAST_VER_CHECK_KEY, SECTION_KEY


def get_version(appctxt):
    """Returns the version of the application"""
    try:
        with open(appctxt.get_resource("base.json"), "r") as fp:
            data = json.load(fp)
        return "v{}".format(data["version"])
    except Exception as e:
        return "v??"


def check_version(appctxt):
    """Returns the release URL if a new version is installed. Otherwise,
    returns False"""
    # first try to read from the config file
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    time_format = "%Y-%m-%d %H:%M:%S"

    # this is tiered as such, so that one missing piece doesn't cause an error
    if SECTION_KEY in config:
        if LAST_VER_CHECK_KEY in config[SECTION_KEY]:
            try:
                # check if last successful version check was less than a day ago.
                # If so, skip
                last_check = datetime.datetime.strptime(
                    config[SECTION_KEY][LAST_VER_CHECK_KEY], time_format
                )
                if last_check > (datetime.datetime.now() - datetime.timedelta(days=1)):
                    return False
            except ValueError:
                pass

    # open the remote url
    url = "https://api.github.com/repos/NathanVaughn/msfs-mod-manager/releases/latest"

    try:
        page = urllib.request.urlopen(url)
    except Exception as e:
        return

    # parse the json
    data = page.read()
    data = data.decode("utf-8")

    try:
        parsed_data = json.loads(data)
        remote_version = parsed_data["tag_name"]
    except:
        return False

    # write the config file back out
    config[SECTION_KEY][LAST_VER_CHECK_KEY] = datetime.datetime.strftime(
        datetime.datetime.now(), time_format
    )
    with open(CONFIG_FILE, "w") as f:
        config.write(f)

    # check if remote version is newer than local version
    if remote_version > get_version(appctxt):
        # if so, return release url
        return parsed_data["html_url"]
    else:
        return False
