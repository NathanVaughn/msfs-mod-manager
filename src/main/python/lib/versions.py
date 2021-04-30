import json
import re
import urllib.parse
import urllib.request
from typing import List, Union

from fbs_runtime.application_context.PySide2 import ApplicationContext
from loguru import logger


def get_app_version(appctxt: ApplicationContext) -> str:
    """
    Returns the version of the application.
    """
    try:
        with open(appctxt.get_resource("base.json"), "r") as fp:
            data = json.load(fp)
        return "v{}".format(data["version"])
    except Exception:
        return "v??"


def get_github_version(
    github_url: str, current_version: str, prerelease_ok: bool
) -> Union[List[str], bool]:
    """
    Returns a list of asset URLs if the latest version on Github
    is newer than the current version. Otherwise returns False.
    """
    logger.debug(f"Trying to check latest version of {github_url}")
    logger.debug(f"Current vesion: {current_version}")

    # accept url in the following forms
    # https://github.com/user/repo
    # https://github.com/user/repo/releases/tags
    # https://github.com/user/repo/issues
    # etc...

    url_path = urllib.parse.urlparse(github_url).path
    # this way, if url is subpage in the repo, won't be affected
    splits = url_path.split("/", 2)

    user = splits[0]
    repo = splits[1]

    # https://docs.github.com/en/rest/reference/repos#list-releases
    api_url = f"https://api.github.com/repos/{user}/{repo}/releases"
    logger.debug(f"Attempting to open url {api_url}")

    # open the remote url
    try:
        page = urllib.request.urlopen(api_url)
    except Exception:
        logger.exception(f"Opening url {api_url} failed")
        return False

    # read page contents
    logger.debug("Reading page contents")
    data = page.read()
    data = data.decode("utf-8")

    logger.debug("Attemping to parse page contents")

    # parse the json
    try:
        parsed_data = json.loads(data)
    except Exception:
        logger.exception("Parsing page contents failed")
        return False

    # find a new release that isn't a prerelease, or latest if prereleases are ok
    target_release = {}
    for release in parsed_data:
        if prerelease_ok or not release["prerelease"]:
            # releases are presented in order, so if we have found a viable
            # release and it's not newer, cancel
            remote_version = release["tag_name"]
            logger.debug(f"Remote version found to be: {remote_version}")
            if remote_version <= current_version:
                return False

            target_release = release
            break

    # if no viable release found, return False
    if not target_release:
        return False

    if "assets" not in target_release:
        # if no assets in release, return source code url
        return [target_release["zipball_url"]]
    else:
        # get all the asset download urls in the target release
        return [asset["browser_download_url"] for asset in target_release["assets"]]


def get_flightsimto_version(
    flighsimto_url: str,
    current_version: str,
) -> Union[str, bool]:
    """
    Returns a download URL if the latest version found on flightsim.to
    is newer than the current version. Otherwise returns False.
    """
    logger.debug(f"Trying to check latest version of {flighsimto_url}")
    logger.debug(f"Current vesion: {current_version}")

    # format one
    # https://flightsim.to/download/tunel-branisko-helipad/13732
    # format two
    # https://flightsim.to/file/13732/tunel-branisko-helipad

    url_path = urllib.parse.urlparse(flighsimto_url).path
    splits = url_path.split("/")

    if splits[0] == "download":
        name = splits[1]
        id_ = splits[2]
    elif splits[0] == "file":
        id_ = splits[1]
        name = splits[2]
    else:
        logger.debug("Unrecognized URL format.")
        return False

    file_url = f"https://flightsim.to/file/{id_}/{name}"
    download_url = f"https://flightsim.to/download/{name}/{id_}"

    # check the version
    logger.debug(f"Attempting to open url {file_url}")

    # open the remote url
    try:
        page = urllib.request.urlopen(file_url)
    except Exception:
        logger.exception(f"Opening url {file_url} failed")
        return False

    # read page contents
    logger.debug("Reading page contents")
    data = page.read()
    data = data.decode("utf-8")

    logger.debug("Attemping to parse page contents")

    # example line of html:
    # <small class="file-small-sub">Current Version 3.0 by <b>PropellerBC</b>
    # I know this is bad, but I only need one line out of the whole document, and
    # don't want to import an entire HTML parser just for this.
    # https://stackoverflow.com/a/1732454
    search = re.search("^.*Current\\sVersion\\s(\\S*)\\s.*$", data)
    if not search:
        return False

    remote_version = search.group(1)
    logger.debug(f"Remote version found to be: {remote_version}")

    if remote_version <= current_version:
        return False

    # I don't expect this trick to work forever
    form_data = urllib.parse.urlencode({}).encode()
    req = urllib.request.Request(download_url, data=form_data)

    logger.debug(f"Attempting to open url {download_url}")

    # open the remote url
    try:
        resp = urllib.request.urlopen(req)
    except Exception:
        logger.exception(f"Opening url {download_url} failed")
        return False

    return resp.url
