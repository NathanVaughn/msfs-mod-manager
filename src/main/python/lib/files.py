import os
import shutil
import stat

import patoolib
from loguru import logger

import lib.config as config
import lib.thread as thread

ARCHIVE_VERBOSITY = -1
ARCHIVE_INTERACTIVE = False

TEMP_FOLDER = os.path.abspath(
    os.path.join(os.getenv("LOCALAPPDATA"), "Temp", "MSFS Mod Manager")
)

if not os.path.exists(config.BASE_FOLDER):
    os.makedirs(config.BASE_FOLDER)


class ExtractionError(Exception):
    """Raised when an archive cannot be extracted.
    Usually due to a missing appropriate extractor program."""


class AccessError(Exception):
    """Raised after an uncorrectable permission error."""


class move_folder_thread(thread.base_thread):
    """Setup a thread to move a folder and not block the main thread."""

    def __init__(self, src, dest):
        """Initialize the folder mover thread."""
        logger.debug("Initialzing folder mover thread")
        function = lambda: move_folder(src, dest, update_func=self.activity_update.emit)
        thread.base_thread.__init__(self, function)


def fix_permissions(folder, update_func=None):
    """Recursively fixes the permissions of a folder so that it can be deleted."""
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


def listdir_dirs(folder, full_paths=False):
    """Returns a list of directories inside of a directory."""
    # logger.debug("Listing directories of {}".format(folder))
    if os.path.isdir(folder):
        result = [
            item
            for item in os.listdir(folder)
            if os.path.isdir(os.path.join(folder, item))
        ]

        if full_paths:
            result = [os.path.join(folder, item) for item in result]

        return result
    else:
        logger.warning("Folder {} does not exist".format(folder))
        return []


def human_readable_size(size, decimal_places=2):
    """Convert number of bytes into human readable value."""
    # https://stackoverflow.com/a/43690506/9944427
    # logger.debug("Converting {} bytes to human readable format".format(size))
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size < 1024.0 or unit == "PB":
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"

def check_same_path(path1, path2):
    """Tests if two paths resolve to the same location."""
    return resolve_symlink(os.path.abspath(path1)) == resolve_symlink(os.path.abspath(path2))

def get_folder_size(folder):
    """Return the size in bytes of a folder, recursively."""
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
    """Deletes a file if it exists."""
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
    """Deletes a folder if it exists."""
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
    """Copies a folder if it exists."""
    logger.debug("Copying folder {} to {}".format(src, dest))
    # check if it exists
    if not os.path.isdir(src):
        logger.warning("Source folder {} does not exist".format(src))
        return

    if check_same_path(src, dest):
        logger.warning("Source folder {} is same as destination folder {}".format(src, dest))
        return

    delete_folder(dest, update_func=update_func)

    # copy the directory
    if update_func:
        update_func(
            "Copying {} to {} ({})".format(
                src, dest, human_readable_size(get_folder_size(src))
            )
        )
    shutil.copytree(src, dest)

def move_folder(src, dest, update_func=None):
    """Copies a folder and deletes the original."""
    if check_same_path(src, dest):
        logger.warning("Source folder {} is same as destination folder {}".format(src, dest))
        return

    logger.debug("Moving folder {} to {}".format(src, dest))
    copy_folder(src, dest, update_func=update_func)
    delete_folder(src, update_func=update_func)


def splitall(path):
    """Splits a path into all its parts."""
    # https://www.oreilly.com/library/view/python-cookbook/0596001673/ch04s16.html
    pieces = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            pieces.insert(0, parts[0])
            break
        elif parts[1] == path:  # sentinel for relative paths
            pieces.insert(0, parts[1])
            break
        else:
            path = parts[0]
            pieces.insert(0, parts[1])
    return pieces


def resolve_symlink(folder):
    """Resolves symlinks in a directory path.
    Basically a quick and dirty reimplementation of os.path.realpath for
    Python versions prior to 3.8."""

    parts = splitall(folder)
    new_path = ""

    # resolve links at every step
    for part in parts:
        new_path = os.path.join(new_path, part)
        if os.path.islink(new_path):
            new_path = os.path.readlink(new_path)

    return new_path


def create_tmp_folder(update_func=None):
    """Deletes existing temp folder if it exists and creates a new one."""
    delete_folder(TEMP_FOLDER, update_func=update_func)
    logger.debug("Creating temp folder {}".format(TEMP_FOLDER))
    os.makedirs(TEMP_FOLDER)


def get_last_open_folder():
    """Gets the last opened directory from the config file."""
    succeeded, value = config.get_key_value(config.LAST_OPEN_FOLDER_KEY)
    if not succeeded or not os.path.isdir(value):
        # if mod cache folder could not be loaded from config
        value = os.path.abspath(os.path.join(os.path.expanduser("~"), "Downloads"))
        config.set_key_value(config.LAST_OPEN_FOLDER_KEY, value)

    return value


def get_mod_cache_folder():
    """Gets the current mod cache folder value from the config file."""
    succeeded, value = config.get_key_value(config.MOD_CACHE_FOLDER_KEY)
    if not succeeded:
        # if mod cache folder could not be loaded from config
        value = os.path.abspath(os.path.join(config.BASE_FOLDER, "modCache"))
        config.set_key_value(config.MOD_CACHE_FOLDER_KEY, value)

    return value


def create_mod_cache_folder():
    """Creates mod cache folder if it does not exist."""
    mod_cache_folder = get_mod_cache_folder()
    if not os.path.exists(mod_cache_folder):
        logger.debug("Creating mod cache folder {}".format(mod_cache_folder))
        os.makedirs(mod_cache_folder)


def extract_archive(archive, folder, update_func=None):
    """Extracts an archive file and returns the output path."""
    if update_func:
        update_func(
            "Extracting archive {} ({})".format(
                archive, human_readable_size(os.path.getsize(archive))
            )
        )

    logger.debug("Extracting archive {} to {}".format(archive, folder))

    try:
        patoolib.extract_archive(
            archive,
            outdir=folder,
            verbosity=ARCHIVE_VERBOSITY,
            interactive=ARCHIVE_INTERACTIVE,
        )

    except patoolib.util.PatoolError as e:
        logger.exception("Unable to extract archive")
        raise ExtractionError(str(e))

    return folder


def create_archive(folder, archive, update_func=None):
    """Creates an archive file and returns the new path."""
    uncomp_size = human_readable_size(get_folder_size(folder))

    if update_func:
        update_func(
            "Creating archive {} ({} uncompressed).\n This will almost certainly take a while.".format(
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
        patoolib.create_archive(
            archive,
            (folder,),
            verbosity=ARCHIVE_VERBOSITY,
            interactive=ARCHIVE_INTERACTIVE,
        )
    except patoolib.util.PatoolError as e:
        logger.exception("Unable to create archive")
        raise ExtractionError(str(e))

    return archive
