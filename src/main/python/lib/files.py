import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys

import patoolib
from loguru import logger

import lib.config as config
import lib.thread as thread

if sys.platform == "win32":
    import win32file

FILE_ATTRIBUTE_REPARSE_POINT = 1024

ARCHIVE_VERBOSITY = -1
ARCHIVE_INTERACTIVE = False
HASH_FILE = "sha256.txt"

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


def fix_path(path):
    """Prepends magic prefix for a path name that is too long"""
    # https://stackoverflow.com/a/50924863
    # this is truly voodoo magic
    magic = "\\\\?\\"

    path = os.path.normpath(path)
    # some semblance of OS-compatibility for those Linux Proton folks
    if os.name == "nt" and not path.startswith(magic):
        return magic + path
    else:
        return path


def fix_permissions(path):
    """Fixes the permissions of a folder or file so that it can be deleted."""
    if not os.path.exists(path):
        logger.warning("Path {} does not exist".format(path))
        return

    # logger.debug("Applying stat.S_IWUSR permission to {}".format(path))
    # fix deletion permission https://blog.nathanv.me/posts/python-permission-issue/
    os.chmod(path, stat.S_IWUSR)


def fix_permissions_recursive(folder, update_func=None):
    """Recursively fixes the permissions of a folder so that it can be deleted."""
    if not os.path.exists(folder):
        logger.warning("Folder {} does not exist".format(folder))
        return

    if update_func:
        update_func("Fixing permissions for {}".format(folder))

    logger.debug("Fixing permissions for {}".format(folder))

    for root, dirs, files in os.walk(folder):
        for d in dirs:
            fix_permissions(os.path.join(root, d))
        for f in files:
            fix_permissions(os.path.join(root, f))


def listdir_dirs(folder, full_paths=False):
    """Returns a list of directories inside of a directory."""
    # logger.debug("Listing directories of {}".format(folder))
    if not os.path.isdir(folder):
        logger.warning("Folder {} does not exist".format(folder))
        return []

    result = [
        item for item in os.listdir(folder) if os.path.isdir(os.path.join(folder, item))
    ]

    if full_paths:
        result = [os.path.join(folder, item) for item in result]

    return result


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
    return resolve_symlink(os.path.abspath(path1)) == resolve_symlink(
        os.path.abspath(path2)
    )


def is_symlink(path):
    """Tests if a path is a symlink."""
    # https://stackoverflow.com/a/52859239
    # http://www.flexhex.com/docs/articles/hard-links.phtml
    if sys.platform != "win32" or sys.getwindowsversion()[0] < 6:
        return os.path.islink(path)

    if os.path.islink(path):
        return True

    return bool(
        os.path.exists(path)
        and win32file.GetFileAttributes(path) & FILE_ATTRIBUTE_REPARSE_POINT
        == FILE_ATTRIBUTE_REPARSE_POINT
    )


def read_symlink(path):
    """Returns the original path of a symlink."""
    if os.path.islink(path):
        return os.path.readlink(path)

    # Pretty slow, avoid if possible
    # TODO, reimplement with Win32
    process = subprocess.run(
        ["cmd", "/c", "fsutil", "reparsepoint", "query", path],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    output = process.stdout.decode("utf-8")
    # https://regex101.com/r/8hc7yq/1
    return re.search("Print Name:\\s+(.+)\\s+Reparse Data", output, re.MULTILINE).group(
        1
    )


def create_symlink(src, dest, update_func=None):
    """Creates a symlink between two directories."""
    if update_func:
        update_func("Creating symlink between {} and {}".format(src, dest))

    # os.symlink(src, dest)
    # TODO, reimplement with Win32

    # delete an existing destination
    if os.path.exists(dest):
        if is_symlink(dest):
            delete_symlink(dest)
        else:
            delete_folder(dest)

    # create the link
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", dest, src],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def delete_symlink(path, update_func=None):
    """Deletes a symlink without removing the directory it is linked to."""
    if update_func:
        update_func("Deleting symlink {} ".format(path))

    # os.unlink(path)
    # TODO, reimplement with Win32

    # remove the link
    subprocess.run(
        ["cmd", "/c", "fsutil", "reparsepoint", "delete", path],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # delete the empty folder
    delete_folder(path)


def get_folder_size(folder):
    """Return the size in bytes of a folder, recursively."""
    # logger.debug("Returning size of {} recursively".format(folder))

    if not os.path.isdir(folder):
        logger.warning("Folder {} does not exist".format(folder))
        return 0

    return sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, _, filenames in os.walk(folder)
        for filename in filenames
    )


def delete_file(file, first=True, update_func=None):
    """Deletes a file if it exists."""
    file = fix_path(file)

    # check if it exists
    if not os.path.isfile(file):
        logger.debug("File {} does not exist".format(file))
        return

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
            fix_permissions(file)
            delete_file(file, first=False, update_func=update_func)
    except FileNotFoundError as e:
        logger.exception(e)
        # try again
        delete_file(file, first=False, update_func=update_func)


def delete_folder(folder, first=True, update_func=None):
    """Deletes a folder if it exists."""
    folder = fix_path(folder)

    # check if it exists
    if not os.path.isdir(folder):
        logger.debug("Folder {} does not exist".format(folder))
        return

    try:
        logger.debug("Attempting to delete folder {}".format(folder))
        # try to delete it
        if update_func:
            update_func("Deleting folder {}".format(folder))
        shutil.rmtree(folder, ignore_errors=False)
    except PermissionError:
        logger.info("Folder deletion failed")
        # if there is a permission error
        if not first:
            logger.error("Not first attempt, raising exception")
            # if not the first attempt, raise error
            raise AccessError(folder)
        else:
            logger.debug("Attempting to fix permissions")
            # otherwise, try to fix permissions and try again
            fix_permissions_recursive(folder, update_func=update_func)
            delete_folder(folder, first=False, update_func=update_func)
    except FileNotFoundError as e:
        logger.exception(e)
        # try again
        delete_folder(folder, first=False, update_func=update_func)


def copy_folder(src, dest, update_func=None):
    """Copies a folder if it exists."""
    src = fix_path(src)
    dest = fix_path(dest)

    logger.debug("Copying folder {} to {}".format(src, dest))
    # check if it exists
    if not os.path.isdir(src):
        logger.warning("Source folder {} does not exist".format(src))
        return

    if check_same_path(src, dest):
        logger.warning(
            "Source folder {} is same as destination folder {}".format(src, dest)
        )
        return

    delete_folder(dest, update_func=update_func)

    # copy the directory
    if update_func:
        update_func(
            "Copying {} to {} ({})".format(
                src, dest, human_readable_size(get_folder_size(src))
            )
        )

    logger.debug("Attempting to copy folder {} to {}".format(src, dest))
    shutil.copytree(src, dest, symlinks=True)


def move_folder(src, dest, update_func=None):
    """Copies a folder and deletes the original."""
    src = fix_path(src)
    dest = fix_path(dest)

    if check_same_path(src, dest):
        logger.warning(
            "Source folder {} is same as destination folder {}".format(src, dest)
        )
        return

    logger.debug("Moving folder {} to {}".format(src, dest))
    copy_folder(src, dest, update_func=update_func)
    delete_folder(src, update_func=update_func)


def resolve_symlink(path):
    """Resolves symlinks in a directory path."""

    if is_symlink(path):
        return read_symlink(path)
    else:
        return path


def create_tmp_folder(update_func=None):
    """Deletes existing temp folder if it exists and creates a new one."""
    delete_folder(TEMP_FOLDER, update_func=update_func)
    logger.debug("Creating temp folder {}".format(TEMP_FOLDER))
    os.makedirs(TEMP_FOLDER)


def get_last_open_folder():
    """Gets the last opened directory from the config file."""
    succeeded, value = config.get_key_value(config.LAST_OPEN_FOLDER_KEY, path=True)
    if not succeeded or not os.path.isdir(value):
        # if mod install folder could not be loaded from config
        value = os.path.abspath(os.path.join(os.path.expanduser("~"), "Downloads"))
        config.set_key_value(config.LAST_OPEN_FOLDER_KEY, value, path=True)

    return fix_path(value)


def get_mod_install_folder():
    """Gets the current mod install folder value from the config file."""
    succeeded, value = config.get_key_value(config.MOD_INSTALL_FOLDER_KEY, path=True)
    if not succeeded:
        # if mod install folder could not be loaded from config
        value = os.path.abspath(os.path.join(config.BASE_FOLDER, "modCache"))
        config.set_key_value(config.MOD_INSTALL_FOLDER_KEY, value, path=True)

    mod_install_folder = fix_path(value)

    if not os.path.exists(mod_install_folder):
        logger.debug("Creating mod install folder {}".format(mod_install_folder))
        os.makedirs(mod_install_folder)

    return mod_install_folder


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
        # rar archives will not work without this
        os.makedirs(folder, exist_ok=True)
        # run the extraction program
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


def hash_file(filename, update_func=None):
    """Returns the hash of a file."""
    # https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
    logger.debug("Hashing {}".format(filename))

    if update_func:
        update_func("Hashing {}".format(filename))

    h = hashlib.sha256()
    with open(filename, "rb", buffering=0) as f:
        b = bytearray(128 * 1024)
        mv = memoryview(b)
        for n in iter(lambda: f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()


def write_hash(folder, h):
    """Writes the hash of a file to the given folder."""
    filename = os.path.join(folder, HASH_FILE)
    with open(filename, "w") as f:
        f.write(h)


def read_hash(folder):
    """Reads the hash of the given folder."""
    filename = os.path.join(folder, HASH_FILE)
    if not os.path.isfile(filename):
        logger.debug("No hash found")
        return None

    with open(filename, "r") as f:
        return f.read()
