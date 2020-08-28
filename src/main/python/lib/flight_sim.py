import configparser
import json
import os
import patoolib
import shutil
import stat

BASE_FOLDER = os.path.abspath(os.path.join(os.getenv("APPDATA"), "MSFS Mod Manager"))
TEMP_FOLDER = os.path.abspath(os.path.join(BASE_FOLDER, ".tmp"))
MOD_CACHE_FOLDER = os.path.abspath(os.path.join(BASE_FOLDER, "modCache"))

CONFIG_FILE = os.path.abspath(os.path.join(BASE_FOLDER, "config.ini"))
SECTION_KEY = "settings"
SIM_PATH_KEY = "sim_path"

if not os.path.exists(BASE_FOLDER):
    os.makedirs(BASE_FOLDER)

class AccessError(Exception):
    pass

class ExtractionError(Exception):
    pass

class NoManifestError(Exception):
    pass

class NoModsError(Exception):
    pass

def fix_permissions(folder):
    """Recursively fixes the permissions of a folder so that it can be deleted"""
    for root, dirs, _ in os.walk(folder):
        for d in dirs:
            os.chmod(os.path.join(root, d), stat.S_IWUSR)

def delete_folder(folder, first=True):
    """Deletes a folder if it exists"""

    # check if it exists
    if os.path.isdir(folder):
        try:
            # try to delete it
            shutil.rmtree(folder)
        except PermissionError:
            # if there is a permission error
            if not first:
                # if not the first attempt, raise error
                raise AccessError(folder)
            else:
                # otherwise, try to fix permissions and try again
                fix_permissions(folder)
                delete_folder(folder, first=False)

def create_tmp_folder():
    """Deletes existing temp folder if it exists and creates a new one"""
    delete_folder(TEMP_FOLDER)
    os.makedirs(TEMP_FOLDER)


def create_mod_cache_folder():
    """Creates mod cache folder if it does not exist"""
    if not os.path.exists(MOD_CACHE_FOLDER):
        os.makedirs(MOD_CACHE_FOLDER)


def is_sim_folder(folder):
    """Returns True/False, whether FlightSimulator.CFG exists inside the
    given directory. Not a perfect tests, but a solid guess."""
    return os.path.isfile(os.path.join(folder, "FlightSimulator.CFG"))


def find_sim_path():
    """Attempts to automatically locate the install location of Flight Simulator.
    Returns None if it fails. Otherwise, returns absolute sim folder path.
    Also returns if reading from config file was successful."""

    # first try to read from the config file
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    # this is tiered as such, so that one missing piece doesn't cause an error
    if SECTION_KEY in config:
        if "sim_path" in config[SECTION_KEY]:
            if is_sim_folder(config[SECTION_KEY][SIM_PATH_KEY]):
                return (config[SECTION_KEY][SIM_PATH_KEY], True)

    # steam detection
    steam_folder = os.path.join(os.getenv("APPDATA"), "Microsoft Flight Simulator")
    if is_sim_folder(steam_folder):
        return (steam_folder, False)

    # ms store detection
    ms_store_folder = os.path.join(
        os.getenv("LOCALAPPDATA"), "Packages", "Microsoft.FlightSimulator_8wekyb3d8bbwe", "LocalCache"
    )
    if is_sim_folder(ms_store_folder):
        return (ms_store_folder, False)

    # last ditch steam detection #1
    steam_folder = os.path.join(os.getenv("PROGRAMFILES(x86)"), "Steam", "steamapps", "common", "MicrosoftFlightSimulator")
    if is_sim_folder(steam_folder):
        return (steam_folder, False)

    # last ditch steam detection #2
    steam_folder = os.path.join(os.getenv("PROGRAMFILES(x86)"), "Steam", "steamapps", "common", "Chucky")
    if is_sim_folder(steam_folder):
        return (steam_folder, False)

    # fail
    return (None, False)


def save_sim_path(sim_folder):
    """Writes sim path to config file"""
    config = configparser.ConfigParser()

    config.add_section(SECTION_KEY)
    config[SECTION_KEY][SIM_PATH_KEY] = sim_folder

    with open(CONFIG_FILE, "w") as f:
        config.write(f)


def sim_mod_folder(sim_folder):
    """Returns the path to the community packages folder inside Flight Simulator"""
    return os.path.join(sim_folder, "Packages", "Community")


def parse_mod(mod_folder, enabled):
    """Builds the mod metadata as a dictionary. Parsed from the manifest.json"""
    mod_data = {"folder_name": os.path.basename(mod_folder)}

    if not os.path.isfile(os.path.join(mod_folder, "manifest.json")):
        raise NoManifestError(mod_folder)

    with open(os.path.join(mod_folder, "manifest.json"), "r") as f:
        data = json.load(f)

    mod_data["title"] = data["title"]
    mod_data["content_type"] = data["content_type"]
    mod_data["creator"] = data["creator"]
    mod_data["version"] = data["package_version"]
    mod_data["installed"] = enabled

    return mod_data


def get_enabled_mods(sim_folder):
    """Returns data for the enabled mods"""
    enabled_mods = []

    for folder in os.listdir(sim_mod_folder(sim_folder)):
        # parse each mod
        enabled_mods.append(
            parse_mod(os.path.join(sim_mod_folder(sim_folder), folder), True)
        )

    return enabled_mods


def get_disabled_mods():
    """Returns data for the disabled mods"""
    # ensure cache folder already exists
    create_mod_cache_folder()

    disabled_mods = []

    for folder in os.listdir(MOD_CACHE_FOLDER):
        # parse each mod
        disabled_mods.append(parse_mod(os.path.join(MOD_CACHE_FOLDER, folder), False))

    return disabled_mods


def unpack_archive(mod_archive):
    """Unpacks an archive file into a temp directory, and returns the new path"""

    # create a temp directory if it does not exist
    create_tmp_folder()
    # determine the base name of the archive
    basefilename = os.path.splitext(os.path.basename(mod_archive))[0]

    # extract the archive
    extracted_archive = os.path.join(TEMP_FOLDER, basefilename)
    try:
        patoolib.extract_archive(mod_archive, outdir=extracted_archive)
        return extracted_archive
    except patoolib.util.PatoolError:
        raise ExtractionError(mod_archive)

def determine_mod_folders(folder):
    """Walks a directory to find the folder(s) with a manifest.json file in them"""
    mod_folders = []

    for root, dirs, _ in os.walk(folder):
        # go through each directory and check for the manifest
        for d in dirs:
            if os.path.isfile(os.path.join(root, d, "manifest.json")):
                mod_folders.append(os.path.join(root, d))

    if not mod_folders:
        raise NoModsError(folder)

    return mod_folders


def install_mod(sim_folder, mod_archive):
    """Extracts and installs a new mod"""
    # extract the archive
    extracted_archive = unpack_archive(mod_archive)
    # determine the mods inside the extracted archive
    mod_folders = determine_mod_folders(extracted_archive)

    installed_mods = []

    for mod_folder in mod_folders:
        # get the base folder name
        base_mod_folder = os.path.basename(mod_folder)
        dest_folder = os.path.join(sim_mod_folder(sim_folder), base_mod_folder)

        # delete mod install if it already exists
        delete_folder(dest_folder)

        # copy mod to sim
        shutil.copytree(mod_folder, dest_folder)
        # remove tmp extracted folder
        delete_folder(mod_folder)

        installed_mods.append(base_mod_folder)

    # return installed mods list
    return installed_mods


def enable_mod(sim_folder, mod_folder):
    """Copies mod folder into flight sim install"""
    src_folder = os.path.join(MOD_CACHE_FOLDER, mod_folder)
    dest_folder = os.path.join(sim_mod_folder(sim_folder), mod_folder)

    # delete mod install if it already exists
    delete_folder(dest_folder)

    # copy mod to sim
    shutil.copytree(src_folder, dest_folder)
    # remove from mod cache
    delete_folder(src_folder)


def disable_mod(sim_folder, mod_folder):
    """Copies mod folder into mod cache"""
    create_mod_cache_folder()

    src_folder = os.path.join(sim_mod_folder(sim_folder), mod_folder)
    dest_folder = os.path.join(MOD_CACHE_FOLDER, mod_folder)

    # delete mod cache if it already exists
    delete_folder(dest_folder)

    # copy mod to mod cache
    shutil.copytree(src_folder, dest_folder)
    # remove from sim
    delete_folder(src_folder)
