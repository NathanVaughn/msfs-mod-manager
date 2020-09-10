import datetime
import json
import os
import shutil
import stat

from loguru import logger
import patoolib
import PySide2.QtCore as QtCore

import lib.config as config

TEMP_FOLDER = os.path.abspath(
    os.path.join(os.getenv("LOCALAPPDATA"), "Temp", "MSFS Mod Manager")
)
MOD_CACHE_FOLDER = os.path.abspath(os.path.join(config.BASE_FOLDER, "modCache"))

if not os.path.exists(config.BASE_FOLDER):
    os.makedirs(config.BASE_FOLDER)


class AccessError(Exception):
    """Raised after an uncorrectable permission error"""

    pass


class ExtractionError(Exception):
    """Raised when an archive cannot be extracted.
    Usually due to a missing appropriate extractor program"""

    pass


class LayoutError(Exception):
    """Raised when a layout.json file cannot be parsed for a mod """

    pass


class NoLayoutError(Exception):
    """Raised when a layout.json file cannot be found for a mod"""

    pass


class ManifestError(Exception):
    """Raised when a manifest.json file cannot be parsed for a mod"""

    pass


class NoManifestError(Exception):
    """Raised when a manifest.json file cannot be found for a mod"""

    pass


class NoModsError(Exception):
    """Raised when no mods are found in an archive"""

    pass


class install_mods_thread(QtCore.QThread):
    """Setup a thread to install mods with and not block the main thread"""

    activity_update = QtCore.Signal(object)
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(Exception)

    def __init__(self, sim_folder, extracted_archive):
        logger.debug("Initialzing mod installer thread")
        QtCore.QThread.__init__(self)
        self.sim_folder = sim_folder
        self.extracted_archive = extracted_archive

    def run(self):
        logger.debug("Running mod installer thread")
        try:
            output = install_mods(
                self.sim_folder,
                self.extracted_archive,
                update_func=self.activity_update.emit,
            )
            self.finished.emit(output)
        except Exception as e:
            self.failed.emit(e)
        logger.debug("Mod installer thread completed")


class install_mod_archive_thread(QtCore.QThread):
    """Setup a thread to install mod archive with and not block the main thread"""

    activity_update = QtCore.Signal(object)
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(Exception)

    def __init__(self, sim_folder, mod_archive):
        logger.debug("Initialzing mod archive installer thread")
        QtCore.QThread.__init__(self)
        self.sim_folder = sim_folder
        self.mod_archive = mod_archive

    def run(self):
        logger.debug("Running mod archive installer thread")
        try:
            output = install_mod_archive(
                self.sim_folder, self.mod_archive, update_func=self.activity_update.emit
            )
            self.finished.emit(output)
        except Exception as e:
            self.failed.emit(e)
        logger.debug("Mod archive installer thread completed")


class uninstall_mod_thread(QtCore.QThread):
    """Setup a thread to uninstall mods with and not block the main thread"""

    activity_update = QtCore.Signal(object)
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(Exception)

    def __init__(self, sim_folder, mod_folder, enabled):
        logger.debug("Initialzing mod uninstaller thread")
        QtCore.QThread.__init__(self)
        self.sim_folder = sim_folder
        self.mod_folder = mod_folder
        self.enabled = enabled

    def run(self):
        logger.debug("Running mod uninstaller thread")
        try:
            output = uninstall_mod(
                self.sim_folder,
                self.mod_folder,
                self.enabled,
                update_func=self.activity_update.emit,
            )
            self.finished.emit(output)
        except Exception as e:
            self.failed.emit(e)
        logger.debug("Mod uninstaller thread completed")


class enable_mod_thread(QtCore.QThread):
    """Setup a thread to enable mods with and not block the main thread"""

    activity_update = QtCore.Signal(object)
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(Exception)

    def __init__(self, sim_folder, mod_folder):
        logger.debug("Initialzing mod enabler thread")
        QtCore.QThread.__init__(self)
        self.sim_folder = sim_folder
        self.mod_folder = mod_folder

    def run(self):
        logger.debug("Running mod enabler thread")
        try:
            output = enable_mod(
                self.sim_folder, self.mod_folder, update_func=self.activity_update.emit
            )
            self.finished.emit(output)
        except Exception as e:
            self.failed.emit(e)
        logger.debug("Mod enabler thread completed")


class disable_mod_thread(QtCore.QThread):
    """Setup a thread to disable mods with and not block the main thread"""

    activity_update = QtCore.Signal(object)
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(Exception)

    def __init__(self, sim_folder, archive):
        logger.debug("Initialzing mod disabler thread")
        QtCore.QThread.__init__(self)
        self.sim_folder = sim_folder
        self.archive = archive

    def run(self):
        logger.debug("Running mod disabler thread")
        try:
            output = disable_mod(
                self.sim_folder, self.archive, update_func=self.activity_update.emit
            )
            self.finished.emit(output)
        except Exception as e:
            self.failed.emit(e)
        logger.debug("Mod disabler thread completed")


class create_backup_thread(QtCore.QThread):
    """Setup a thread to create backup with and not block the main thread"""

    activity_update = QtCore.Signal(object)
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(Exception)

    def __init__(self, sim_folder, mod_folder):
        logger.debug("Initialzing backup creator thread")
        QtCore.QThread.__init__(self)
        self.sim_folder = sim_folder
        self.archive = mod_folder

    def run(self):
        logger.debug("Running backup creator thread")
        try:
            output = create_backup(
                self.sim_folder, self.archive, update_func=self.activity_update.emit
            )
            self.finished.emit(output)
        except Exception as e:
            self.failed.emit(e)
        logger.debug("Mod backup creator completed")


def fix_permissions(folder, update_func=None):
    """Recursively fixes the permissions of a folder so that it can be deleted"""
    if update_func:
        update_func("Fixing permissions for {}".format(folder))

    logger.debug("Fixing permissions for {}".format(folder))

    for root, dirs, files in os.walk(folder):
        for d in dirs:
            logger.debug(
                "Applying stat.S_IWUSR permission to {}".format(os.path.join(root, d))
            )
            os.chmod(os.path.join(root, d), stat.S_IWUSR)
        for f in files:
            logger.debug(
                "Applying stat.S_IWUSR permission to {}".format(os.path.join(root, f))
            )
            os.chmod(os.path.join(root, f), stat.S_IWUSR)


def listdir_dirs(folder):
    """Returns a list of directories inside of a directory"""
    # logger.debug("Listing directories of {}".format(folder))
    if os.path.isdir(folder):
        dirs = []
        for item in os.listdir(folder):
            if os.path.isdir(os.path.join(folder, item)):
                dirs.append(item)

        return dirs
    else:
        logger.warning("Folder {} does not exist".format(folder))
        return []


def human_readable_size(size, decimal_places=2):
    """Convert number of bytes into human readable value"""
    # https://stackoverflow.com/a/43690506/9944427
    # logger.debug("Converting {} bytes to human readable format".format(size))
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size < 1024.0 or unit == "PB":
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def get_folder_size(folder):
    """Return the size in bytes of a folder, recursively"""
    logger.debug("Returning size of {} recursively".format(folder))
    if os.path.isdir(folder):
        return sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, _, filenames in os.walk(folder)
            for filename in filenames
        )
    else:
        logger.warning("Folder {} does not exist".format(folder))
        return 0


def delete_file(file, first=True, update_func=None):
    """Deletes a file if it exists"""
    # check if it exists
    if os.path.isfile(file):
        try:
            logger.debug("Attempting to delete file {}".format(file))
            # try to delete it
            if update_func:
                update_func("Deleting file {}".format(file))
            os.remove(file)
        except PermissionError:
            logger.debug("File deletion failed")
            # if there is a permission error
            if not first:
                logger.error("Not first attempt, raising exception")
                # if not the first attempt, raise error
                raise AccessError(file)
            else:
                logger.debug("Attempting to fix permissions")
                # otherwise, try to fix permissions and try again
                fix_permissions(os.path.dirname(file), update_func=update_func)
                delete_file(file, first=False, update_func=update_func)
    else:
        logger.debug("File {} does not exist".format(file))


def delete_folder(folder, first=True, update_func=None):
    """Deletes a folder if it exists"""
    # check if it exists
    if os.path.isdir(folder):
        try:
            logger.debug("Attempting to delete folder {}".format(folder))
            # try to delete it
            if update_func:
                update_func("Deleting folder {}".format(folder))
            shutil.rmtree(folder)
        except PermissionError:
            logger.debug("Folder deletion failed")
            # if there is a permission error
            if not first:
                logger.error("Not first attempt, raising exception")
                # if not the first attempt, raise error
                raise AccessError(folder)
            else:
                logger.debug("Attempting to fix permissions")
                # otherwise, try to fix permissions and try again
                fix_permissions(folder, update_func=update_func)
                delete_folder(folder, first=False, update_func=update_func)
    else:
        logger.debug("Folder {} does not exist".format(folder))


def copy_folder(src, dest, update_func=None):
    """Copies a folder if it exists"""
    logger.debug("Copying folder {} to {}".format(src, dest))
    # check if it exists
    if os.path.isdir(src):
        delete_folder(dest, update_func=update_func)

        # copy the directory
        if update_func:
            update_func(
                "Copying {} to {} ({})".format(
                    src, dest, human_readable_size(get_folder_size(src))
                )
            )
        shutil.copytree(src, dest)
    else:
        logger.warning("Source folder {} does not exist".format(src))


def move_folder(src, dest, update_func=None):
    """Copies a folder and deletes the original"""
    logger.debug("Moving folder {} to {}".format(src, dest))
    copy_folder(src, dest, update_func=update_func)
    delete_folder(src, update_func=update_func)


def create_tmp_folder(update_func=None):
    """Deletes existing temp folder if it exists and creates a new one"""
    delete_folder(TEMP_FOLDER, update_func=update_func)
    logger.debug("Creating temp folder {}".format(TEMP_FOLDER))
    os.makedirs(TEMP_FOLDER)


def create_mod_cache_folder():
    """Creates mod cache folder if it does not exist"""
    if not os.path.exists(MOD_CACHE_FOLDER):
        logger.debug("Creating mod cache folder {}".format(MOD_CACHE_FOLDER))
        os.makedirs(MOD_CACHE_FOLDER)


def parse_user_cfg(sim_folder=None, filename=None):
    """Parses the given UserCfg.opt file to find the installed packages path
    Returns the path as a string"""

    logger.debug("Parsing UserCfg.opt file")

    if sim_folder:
        filename = os.path.join(sim_folder, "UserCfg.opt")

    installed_packages_path = ""

    with open(filename, "r") as fp:
        for line in fp:
            if line.startswith("InstalledPackagesPath"):
                logger.debug("Found InstalledPackagesPath line: {}".format(line))
                installed_packages_path = line

    # splits the line once, and takes the second instance
    installed_packages_path = installed_packages_path.split(" ", 1)[1].strip()
    # normalize the string
    installed_packages_path = installed_packages_path.strip('"').strip("'")
    # evaluate the path
    installed_packages_path = os.path.realpath(installed_packages_path)

    logger.debug("Path parsed: {}".format(installed_packages_path))

    return installed_packages_path


def is_sim_folder(folder):
    """Returns True/False, whether FlightSimulator.CFG exists inside the
    given directory. Not a perfect tests, but a solid guess."""
    logger.debug("Testing if {} is main MSFS folder".format(folder))
    try:
        status = os.path.isfile(os.path.join(folder, "FlightSimulator.CFG"))
        logger.debug("Folder {} is main MSFS folder: {}".format(folder, status))
        return status
    except Exception as e:
        logger.exception("Checking sim folder status failed")
        return False


def is_sim_packages_folder(folder):
    """Returns whether the given folder is the FS2020 packages folder.
    Not a perfect test, but a decent guess."""
    # test if the folder above it contains both 'Community' and 'Official'
    logger.debug("Testing if {} is MSFS sim packages folder".format(folder))
    try:
        packages_folders = listdir_dirs(folder)
        status = "Official" in packages_folders and "Community" in packages_folders
        logger.debug("Folder {} is MSFS sim packages folder: {}".format(folder, status))
        return status
    except Exception as e:
        logger.exception("Checking sim packages folder status failed")
        return False


def find_sim_folder():
    """Attempts to automatically locate the install
    location of Flight Simulator Packages.
    Returns if reading from config file was successful, and
    returns absolute sim folder path. Otherwise, returns None if it fails"""

    logger.debug("Attempting to automatically locate simulator path")

    # first try to read from the config file
    logger.debug("Trying to find simulator path from config file")
    succeed, value = config.get_key_value(config.SIM_FOLDER_KEY)
    if succeed and is_sim_packages_folder(value):
        logger.debug("Config file sim path found and valid")
        return (True, value)

    # steam detection
    logger.debug("Trying to find simulator path from default Steam install")
    steam_folder = os.path.join(os.getenv("APPDATA"), "Microsoft Flight Simulator")
    if is_sim_folder(steam_folder):
        steam_packages_folder = os.path.join(parse_user_cfg(sim_folder=steam_folder))
        if is_sim_packages_folder(steam_packages_folder):
            logger.debug("Steam sim path found and valid")
            return (False, steam_packages_folder)

    # ms store detection
    logger.debug("Trying to find simulator path from default MS Store install")
    ms_store_folder = os.path.join(
        os.getenv("LOCALAPPDATA"),
        "Packages",
        "Microsoft.FlightSimulator_8wekyb3d8bbwe",
        "LocalCache",
    )
    if is_sim_folder(ms_store_folder):
        ms_store_packages_folder = os.path.join(
            parse_user_cfg(sim_folder=ms_store_folder)
        )
        if is_sim_packages_folder(ms_store_packages_folder):
            logger.debug("MS Store sim path found and valid")
            return (False, ms_store_packages_folder)

    # boxed edition detection
    logger.debug("Trying to find simulator path from default boxed edition install")
    boxed_packages_folder = os.path.join(os.getenv("LOCALAPPDATA"), "MSFSPackages")
    if is_sim_packages_folder(boxed_packages_folder):
        logger.debug("Boxed edition sim path found and valid")
        return (False, boxed_packages_folder)

    # last ditch steam detection #1
    logger.debug("Trying to find simulator path from last-ditch Steam install #1")
    steam_folder = os.path.join(
        os.getenv("PROGRAMFILES(x86)"),
        "Steam",
        "steamapps",
        "common",
        "MicrosoftFlightSimulator",
    )
    if is_sim_folder(steam_folder):
        steam_packages_folder = os.path.join(parse_user_cfg(sim_folder=steam_folder))
        if is_sim_packages_folder(steam_packages_folder):
            logger.debug("Last-ditch #1 Steam sim path found and valid")
            return (False, steam_packages_folder)

    # last ditch steam detection #2
    logger.debug("Trying to find simulator path from last-ditch Steam install #2")
    steam_folder = os.path.join(
        os.getenv("PROGRAMFILES(x86)"),
        "Steam",
        "steamapps",
        "common",
        "Chucky",
    )
    if is_sim_folder(steam_folder):
        steam_packages_folder = os.path.join(parse_user_cfg(sim_folder=steam_folder))
        if is_sim_packages_folder(steam_packages_folder):
            logger.debug("Last-ditch #2 Steam sim path found and valid")
            return (False, steam_packages_folder)

    # fail
    logger.warning("Simulator path could not be automatically determined")
    return (False, None)


def sim_mod_folder(sim_folder):
    """Returns the path to the community packages folder inside Flight Simulator.
    Tries to resolve symlinks in every step of the path"""
    # logger.debug("Determining path for sim community packages folder")

    if os.path.islink(sim_folder):
        # logger.debug("Sim path {} is a symlink. Resolving.".format(sim_folder))
        sim_folder = os.readlink(sim_folder)

    step_2 = os.path.join(sim_folder, "Community")
    if os.path.islink(step_2):
        # logger.debug("Community packages {} is a symlink. Resolving.".format(step_2))
        step_2 = os.readlink(step_2)

    # logger.debug("Final sim community packages folder path: {}".format(step_2))
    return step_2


def get_mod_folder(sim_folder, folder, enabled):
    """Returns path to mod folder given folder name and enabled status"""
    # logger.debug("Determining path for mod {}, enabled: {}".format(folder, enabled))

    if enabled:
        mod_folder = os.path.join(sim_mod_folder(sim_folder), folder)
    else:
        mod_folder = os.path.join(MOD_CACHE_FOLDER, folder)

    # logger.debug("Final mod path: {}".format(mod_folder))

    return mod_folder


def parse_mod_layout(sim_folder, folder, enabled):
    """Builds the mod files info as a dictionary. Parsed from the layout.json"""
    mod_folder = get_mod_folder(sim_folder, folder, enabled)
    logger.debug("Parsing layout for {}".format(mod_folder))

    if not os.path.isfile(os.path.join(mod_folder, "layout.json")):
        logger.error("No layout.json found")
        raise NoLayoutError(mod_folder)

    with open(os.path.join(mod_folder, "layout.json"), "r") as f:
        try:
            data = json.load(f)
        except Exception as e:
            logger.exception("layout.json could not be parsed")
            raise LayoutError(e)

    return data["content"]


def parse_mod_files(sim_folder, folder, enabled):
    """Builds the mod files info as a dictionary. Parsed from the layout.json"""
    mod_folder = get_mod_folder(sim_folder, folder, enabled)
    logger.debug("Parsing all mod files for {}".format(mod_folder))

    data = []
    for root, _, files in os.walk(mod_folder):
        for file in files:
            data.append(
                {
                    "path": os.path.join(os.path.relpath(root, mod_folder), file),
                    "size": os.path.getsize(os.path.join(root, file)),
                }
            )

    return data


def parse_mod_manifest(sim_folder, folder, enabled):
    """Builds the mod metadata as a dictionary. Parsed from the manifest.json"""
    mod_folder = get_mod_folder(sim_folder, folder, enabled)
    logger.debug("Parsing manifest for {}".format(mod_folder))

    mod_data = {"folder_name": os.path.basename(mod_folder)}
    manifest_path = os.path.join(mod_folder, "manifest.json")

    if not os.path.isfile(manifest_path):
        logger.error("No manifest.json found")
        raise NoManifestError(mod_folder)

    with open(manifest_path, "r") as f:
        try:
            data = json.load(f)
        except Exception as e:
            logger.exception("manifest.json could not be parsed")
            raise ManifestError(e)

    # manifest data
    mod_data["content_type"] = data.get("content_type", "")
    mod_data["title"] = data.get("title", "")
    mod_data["manufacturer"] = data.get("manufacturer", "")
    mod_data["creator"] = data.get("creator", "")
    mod_data["version"] = data.get("package_version", "")
    mod_data["minimum_game_version"] = data.get("minimum_game_version", "")

    # manifest metadata
    # Windows considering moving/copying a file 'creating' it again, and not modifying
    # contents
    mod_data["time_mod"] = datetime.datetime.fromtimestamp(
        os.path.getctime(manifest_path)
    ).strftime("%Y-%m-%d %H:%M:%S")
    mod_data["enabled"] = enabled

    return mod_data


def get_enabled_mods(sim_folder):
    """Returns data for the enabled mods"""
    logger.debug("Retrieving list of enabled mods")
    enabled_mods = []

    for folder in listdir_dirs(sim_mod_folder(sim_folder)):
        # parse each mod
        enabled_mods.append(parse_mod_manifest(sim_folder, folder, True))

    return enabled_mods


def get_disabled_mods(sim_folder):
    """Returns data for the disabled mods"""
    logger.debug("Retrieving list of disabled mods")
    # ensure cache folder already exists
    create_mod_cache_folder()

    disabled_mods = []

    for folder in listdir_dirs(MOD_CACHE_FOLDER):
        # parse each mod
        disabled_mods.append(parse_mod_manifest(sim_folder, folder, False))

    return disabled_mods


def create_archive(folder, archive, update_func=None):
    """Creates an archive file and returns the new path"""
    uncomp_size = human_readable_size(get_folder_size(folder))

    if update_func:
        update_func(
            "Creating archive {}, {} uncompressed.\n This will almost certainly take a while.".format(
                archive, uncomp_size
            )
        )

    # delete the archive if it already exists,
    # as patoolib will refuse to overwrite an existing archive
    delete_file(archive, update_func=update_func)

    logger.debug("Creating archive {}".format(archive))
    # create the archive
    try:
        # this expects files/folders in a list
        patoolib.create_archive(archive, (folder,), verbosity=-1, interactive=False)
    except patoolib.util.PatoolError:
        logger.exception("Unable to create archive")
        raise ExtractionError(archive)

    return archive


def extract_archive(archive, update_func=None):
    """Extracts an archive file into a temp directory and returns the new path"""
    logger.debug("Extracting archive {}".format(archive))
    # create a temp directory if it does not exist
    create_tmp_folder(update_func=update_func)
    # determine the base name of the archive
    basefilename = os.path.splitext(os.path.basename(archive))[0]

    # extract the archive
    extracted_archive = os.path.join(TEMP_FOLDER, basefilename)
    try:
        if update_func:
            update_func("Extracting archive {}".format(archive))

        logger.debug("Extracting archive {} to {}".format(archive, extract_archive))

        patoolib.extract_archive(
            archive, outdir=extracted_archive, verbosity=-1, interactive=False
        )

        return extracted_archive
    except patoolib.util.PatoolError:
        logger.exception("Unable to extract archive")
        raise ExtractionError(archive)


def determine_mod_folders(folder, update_func=None):
    """Walks a directory to find the folder(s) with a manifest.json file in them"""
    logger.debug("Locating mod folders inside {}".format(folder))
    mod_folders = []

    if update_func:
        update_func("Locating mods inside {}".format(folder))

    # check the root folder for a manifest
    if os.path.isfile(os.path.join(folder, "manifest.json")):
        logger.debug("Mod found {}".format(os.path.join(folder)))
        mod_folders.append(os.path.join(folder))

    for root, dirs, _ in os.walk(folder):
        # go through each directory and check for the manifest
        for d in dirs:
            if os.path.isfile(os.path.join(root, d, "manifest.json")):
                logger.debug("Mod found {}".format(os.path.join(root, d)))
                mod_folders.append(os.path.join(root, d))

    if not mod_folders:
        logger.error("No mods found")
        raise NoModsError(folder)

    return mod_folders


def install_mods(sim_folder, extracted_archive, update_func=None):
    """Extracts and installs a new mod"""
    logger.debug("Installing mod {}".format(extracted_archive))

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


def install_mod_archive(sim_folder, mod_archive, update_func=None):
    """Extracts and installs a new mod"""
    logger.debug("Installing mod {}".format(mod_archive))
    # extract the archive
    extracted_archive = extract_archive(mod_archive, update_func=update_func)

    return install_mods(sim_folder, extracted_archive, update_func=update_func)


def uninstall_mod(sim_folder, mod_folder, enabled, update_func=None):
    """Uninstalls a mod"""
    logger.debug("Uninstalling mod {}".format(mod_folder))
    # delete folder
    delete_folder(
        get_mod_folder(sim_folder, mod_folder, enabled), update_func=update_func
    )


def enable_mod(sim_folder, mod_folder, update_func=None):
    """Copies mod folder into flight sim install"""
    logger.debug("Enabling mod {}".format(mod_folder))
    src_folder = os.path.join(MOD_CACHE_FOLDER, mod_folder)
    dest_folder = os.path.join(sim_mod_folder(sim_folder), mod_folder)

    # move mod to sim
    move_folder(src_folder, dest_folder, update_func=update_func)


def disable_mod(sim_folder, mod_folder, update_func=None):
    """Copies mod folder into mod cache"""
    logger.debug("Disabling mod {}".format(mod_folder))
    create_mod_cache_folder()

    src_folder = os.path.join(sim_mod_folder(sim_folder), mod_folder)
    dest_folder = os.path.join(MOD_CACHE_FOLDER, mod_folder)

    # move mod to mod cache
    move_folder(src_folder, dest_folder, update_func=update_func)


def create_backup(sim_folder, archive, update_func=None):
    """Creates a backup of all enabled mods"""
    return create_archive(sim_mod_folder(sim_folder), archive, update_func=update_func)
