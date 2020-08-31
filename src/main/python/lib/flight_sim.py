import configparser
import json
import os
import shutil
import stat

import patoolib
import PySide2.QtCore as QtCore

BASE_FOLDER = os.path.abspath(os.path.join(os.getenv("APPDATA"), "MSFS Mod Manager"))
TEMP_FOLDER = os.path.abspath(os.path.join(BASE_FOLDER, ".tmp"))
MOD_CACHE_FOLDER = os.path.abspath(os.path.join(BASE_FOLDER, "modCache"))

CONFIG_FILE = os.path.abspath(os.path.join(BASE_FOLDER, "config.ini"))
SECTION_KEY = "settings"
SIM_PATH_KEY = "sim_path"

if not os.path.exists(BASE_FOLDER):
    os.makedirs(BASE_FOLDER)


class AccessError(Exception):
    """Raised after an uncorrectable permission error"""

    pass


class ExtractionError(Exception):
    """Raised when an archive cannot be extracted.
    Usually due to a missing appropriate extractor program"""

    pass


class NoLayoutError(Exception):
    """Raised when a layout.json file cannot be found for a mod"""

    pass


class NoManifestError(Exception):
    """Raised when a manifest.json file cannot be found for a mod"""

    pass


class NoModsError(Exception):
    """Raised when no mods are found in an archive"""

    pass


class install_mod_thread(QtCore.QThread):
    """Setup a thread to install mods with to not block the main thread"""

    activity_update = QtCore.Signal(object)
    finished = QtCore.Signal(object)

    def __init__(self, sim_path, mod_archive):
        QtCore.QThread.__init__(self)
        self.sim_path = sim_path
        self.mod_archive = mod_archive

    def run(self):
        output = install_mod(
            self.sim_path, self.mod_archive, update_func=self.activity_update.emit
        )
        self.finished.emit(output)


class uninstall_mod_thread(QtCore.QThread):
    """Setup a thread to uninstall mods with to not block the main thread"""

    activity_update = QtCore.Signal(object)
    finished = QtCore.Signal(object)

    def __init__(self, sim_path, mod_folder, enabled):
        QtCore.QThread.__init__(self)
        self.sim_path = sim_path
        self.mod_folder = mod_folder
        self.enabled = enabled

    def run(self):
        output = uninstall_mod(
            self.sim_path,
            self.mod_folder,
            self.enabled,
            update_func=self.activity_update.emit,
        )
        self.finished.emit(output)


class enable_mod_thread(QtCore.QThread):
    """Setup a thread to enable mods with to not block the main thread"""

    activity_update = QtCore.Signal(object)
    finished = QtCore.Signal(object)

    def __init__(self, sim_path, mod_folder):
        QtCore.QThread.__init__(self)
        self.sim_path = sim_path
        self.mod_archive = mod_folder

    def run(self):
        output = enable_mod(
            self.sim_path, self.mod_archive, update_func=self.activity_update.emit
        )
        self.finished.emit(output)


class disable_mod_thread(QtCore.QThread):
    """Setup a thread to disable mods with to not block the main thread"""

    activity_update = QtCore.Signal(object)
    finished = QtCore.Signal(object)

    def __init__(self, sim_path, mod_folder):
        QtCore.QThread.__init__(self)
        self.sim_path = sim_path
        self.mod_archive = mod_folder

    def run(self):
        output = disable_mod(
            self.sim_path, self.mod_archive, update_func=self.activity_update.emit
        )
        self.finished.emit(output)


def fix_permissions(folder, update_func=None):
    """Recursively fixes the permissions of a folder so that it can be deleted"""
    if update_func:
        update_func("Fixing permissions for {}".format(folder))

    for root, dirs, files in os.walk(folder):
        for d in dirs:
            os.chmod(os.path.join(root, d), stat.S_IWUSR)
        for f in files:
            os.chmod(os.path.join(root, f), stat.S_IWUSR)


def listdir_dirs(folder):
    """Returns a list of directories inside of a directory"""
    dirs = []
    for item in os.listdir(folder):
        if os.path.isdir(os.path.join(folder, item)):
            dirs.append(item)

    return dirs


def delete_folder(folder, first=True, update_func=None):
    """Deletes a folder if it exists"""
    # check if it exists
    if os.path.isdir(folder):
        try:
            # try to delete it
            if update_func:
                update_func("Deleting directory {}".format(folder))
            shutil.rmtree(folder)
        except PermissionError:
            # if there is a permission error
            if not first:
                # if not the first attempt, raise error
                raise AccessError(folder)
            else:
                # otherwise, try to fix permissions and try again
                fix_permissions(folder, update_func=update_func)
                delete_folder(folder, first=False, update_func=update_func)


def copy_folder(src, dest, update_func=None):
    """Copies a folder if it exists"""
    # check if it exists
    if os.path.isdir(src):
        delete_folder(dest, update_func=update_func)

        # copy the directory
        if update_func:
            update_func("Copying {} to {}".format(src, dest))
        shutil.copytree(src, dest)


def move_folder(src, dest, update_func=None):
    """Copies a folder and deletes the original"""
    # check if it exists
    copy_folder(src, dest, update_func=update_func)
    delete_folder(src, update_func=update_func)


def create_tmp_folder(update_func=None):
    """Deletes existing temp folder if it exists and creates a new one"""
    delete_folder(TEMP_FOLDER, update_func=update_func)
    os.makedirs(TEMP_FOLDER)


def create_mod_cache_folder():
    """Creates mod cache folder if it does not exist"""
    if not os.path.exists(MOD_CACHE_FOLDER):
        os.makedirs(MOD_CACHE_FOLDER)


def parse_user_cfg(sim_folder=None, filename=None):
    """Parses the given UserCfg.opt file to find the installed packages path
    Returns the path as a string"""

    if sim_folder:
        filename = os.path.join(sim_folder, "UserCfg.opt")

    installed_packages_path = ""

    with open(filename, "r") as fp:
        for line in fp:
            if line.startswith("InstalledPackagesPath"):
                installed_packages_path = line

    # splits the line once, and takes the second instance
    installed_packages_path = installed_packages_path.split(" ", 1)[1].strip()
    # normalize the string
    installed_packages_path = installed_packages_path.strip('"').strip("'")
    # evaluate the path
    installed_packages_path = os.path.realpath(installed_packages_path)

    return installed_packages_path


def is_sim_folder(folder):
    """Returns True/False, whether FlightSimulator.CFG exists inside the
    given directory. Not a perfect tests, but a solid guess."""
    try:
        return os.path.isfile(os.path.join(folder, "FlightSimulator.CFG"))
    except Exception as e:
        return False


def is_sim_packages_folder(folder):
    """Returns whether the given folder is the FS2020 packages folder.
    Not a perfect test, but a decent guess."""
    # test if the folder above it contains both 'Community' and 'Official'
    try:
        packages_folders = os.listdir(folder)
        return "Official" in packages_folders and "Community" in packages_folders
    except Exception as e:
        return False


def find_sim_path():
    """Attempts to automatically locate the install
    location of Flight Simulator Packages.
    Returns None if it fails. Otherwise, returns absolute sim folder path.
    Also returns if reading from config file was successful."""

    # first try to read from the config file
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    # this is tiered as such, so that one missing piece doesn't cause an error
    if SECTION_KEY in config:
        if "sim_path" in config[SECTION_KEY]:
            if is_sim_packages_folder(config[SECTION_KEY][SIM_PATH_KEY]):
                return (config[SECTION_KEY][SIM_PATH_KEY], True)

    # steam detection
    steam_folder = os.path.join(os.getenv("APPDATA"), "Microsoft Flight Simulator")
    if is_sim_folder(steam_folder):
        steam_packages_folder = os.path.join(parse_user_cfg(sim_folder=steam_folder))
        if is_sim_packages_folder(steam_packages_folder):
            return (steam_packages_folder, False)

    # ms store detection
    ms_store_folder = os.path.join(
        os.getenv("LOCALAPPDATA"),
        "Packages",
        "Microsoft.FlightSimulator_8wekyb3d8bbwe",
        "LocalCache",
        "Packages",
    )
    if is_sim_folder(ms_store_folder):
        ms_store_packages_folder = os.path.join(
            parse_user_cfg(sim_folder=ms_store_folder)
        )
        if is_sim_packages_folder(ms_store_packages_folder):
            return (ms_store_folder, False)

    # last ditch steam detection #1
    steam_folder = os.path.join(
        os.getenv("PROGRAMFILES(x86)"),
        "Steam",
        "steamapps",
        "common",
        "MicrosoftFlightSimulator",
        "Packages",
    )
    if is_sim_folder(steam_folder):
        steam_packages_folder = os.path.join(parse_user_cfg(sim_folder=steam_folder))
        if is_sim_packages_folder(steam_packages_folder):
            return (steam_packages_folder, False)

    # last ditch steam detection #2
    steam_folder = os.path.join(
        os.getenv("PROGRAMFILES(x86)"),
        "Steam",
        "steamapps",
        "common",
        "Chucky",
        "Packages",
    )
    if is_sim_folder(steam_folder):
        steam_packages_folder = os.path.join(parse_user_cfg(sim_folder=steam_folder))
        if is_sim_packages_folder(steam_packages_folder):
            return (steam_packages_folder, False)

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
    """Returns the path to the community packages folder inside Flight Simulator.
    Tries to resolve symlinks in every step of the path"""
    if os.path.islink(sim_folder):
        sim_folder = os.readlink(sim_folder)

    step_2 = os.path.join(sim_folder, "Community")
    if os.path.islink(step_2):
        step_2 = os.readlink(step_2)

    return step_2


def parse_mod_manifest(mod_folder, enabled):
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

    for folder in listdir_dirs(sim_mod_folder(sim_folder)):
        # parse each mod
        enabled_mods.append(
            parse_mod_manifest(os.path.join(sim_mod_folder(sim_folder), folder), True)
        )

    return enabled_mods


def get_disabled_mods():
    """Returns data for the disabled mods"""
    # ensure cache folder already exists
    create_mod_cache_folder()

    disabled_mods = []

    for folder in listdir_dirs(MOD_CACHE_FOLDER):
        # parse each mod
        disabled_mods.append(
            parse_mod_manifest(os.path.join(MOD_CACHE_FOLDER, folder), False)
        )

    return disabled_mods


def extract_archive(mod_archive, update_func=None):
    """Extracts an archive file into a temp directory, and returns the new path"""
    # create a temp directory if it does not exist
    create_tmp_folder(update_func=update_func)
    # determine the base name of the archive
    basefilename = os.path.splitext(os.path.basename(mod_archive))[0]

    # extract the archive
    extracted_archive = os.path.join(TEMP_FOLDER, basefilename)
    try:
        if update_func:
            update_func("Extracting archive {}".format(mod_archive))

        patoolib.extract_archive(
            mod_archive,
            outdir=extracted_archive,
            verbosity=-1,
        )

        return extracted_archive
    except patoolib.util.PatoolError:
        raise ExtractionError(mod_archive)


def determine_mod_folders(folder, update_func=None):
    """Walks a directory to find the folder(s) with a manifest.json file in them"""
    mod_folders = []

    if update_func:
        update_func("Locating mods inside {}".format(folder))

    for root, dirs, _ in os.walk(folder):
        # go through each directory and check for the manifest
        for d in dirs:
            if os.path.isfile(os.path.join(root, d, "manifest.json")):
                mod_folders.append(os.path.join(root, d))

    if not mod_folders:
        raise NoModsError(folder)

    return mod_folders


def install_mod(sim_folder, mod_archive, update_func=None):
    """Extracts and installs a new mod"""
    # extract the archive
    extracted_archive = extract_archive(mod_archive, update_func=update_func)

    # determine the mods inside the extracted archive
    mod_folders = determine_mod_folders(extracted_archive, update_func=update_func)

    installed_mods = []

    for mod_folder in mod_folders:
        # get the base folder name
        base_mod_folder = os.path.basename(mod_folder)
        dest_folder = os.path.join(sim_mod_folder(sim_folder), base_mod_folder)

        # move mod to sim
        move_folder(mod_folder, dest_folder, update_func=update_func)

        installed_mods.append(base_mod_folder)

    # return installed mods list
    return installed_mods


def uninstall_mod(sim_folder, mod_folder, enabled, update_func=None):
    """Uninstalls a mod"""
    if enabled:
        src_folder = os.path.join(sim_mod_folder(sim_folder), mod_folder)
    else:
        src_folder = os.path.join(MOD_CACHE_FOLDER, mod_folder)

    # delete folder
    delete_folder(src_folder, update_func=update_func)


def enable_mod(sim_folder, mod_folder, update_func=None):
    """Copies mod folder into flight sim install"""
    src_folder = os.path.join(MOD_CACHE_FOLDER, mod_folder)
    dest_folder = os.path.join(sim_mod_folder(sim_folder), mod_folder)

    # move mod to sim
    move_folder(src_folder, dest_folder, update_func=update_func)


def disable_mod(sim_folder, mod_folder, update_func=None):
    """Copies mod folder into mod cache"""
    create_mod_cache_folder()

    src_folder = os.path.join(sim_mod_folder(sim_folder), mod_folder)
    dest_folder = os.path.join(MOD_CACHE_FOLDER, mod_folder)

    # move mod to mod cache
    move_folder(src_folder, dest_folder, update_func=update_func)
