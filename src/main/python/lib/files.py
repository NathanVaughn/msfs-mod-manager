import os
import shutil
import stat

from loguru import logger

import lib.config as config

TEMP_FOLDER = os.path.abspath(
    os.path.join(os.getenv("LOCALAPPDATA"), "Temp", "MSFS Mod Manager")
)

if not os.path.exists(config.BASE_FOLDER):
    os.makedirs(config.BASE_FOLDER)


class AccessError(Exception):
    """Raised after an uncorrectable permission error."""


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


def listdir_dirs(folder):
    """Returns a list of directories inside of a directory."""
    # logger.debug("Listing directories of {}".format(folder))
    if os.path.isdir(folder):
        return [
            item
            for item in os.listdir(folder)
            if os.path.isdir(os.path.join(folder, item))
        ]

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
    """Copies a folder and deletes the original."""
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
    Basically a quick  and dirty reimplementation of os.path.realpath for Python
    before 3.8."""

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
