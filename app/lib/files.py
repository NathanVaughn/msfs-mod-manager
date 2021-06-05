import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Callable, Union

import patoolib
from loguru import logger

Num = Union[float, int]

# https://stackoverflow.com/a/50924863
# this is truly voodoo magic
MAGIC = "\\\\?\\"

# ======================================================================================
# Exceptions
# ======================================================================================


class ExtractionError(Exception):
    """
    Raised when an archive cannot be extracted.
    Usually due to a missing appropriate extractor program.
    """


# ======================================================================================
# Magic
# ======================================================================================


def magic(path: Path) -> Path:
    """
    Adds magic Windows prefix that allows support of paths longer than 256 characters.
    """
    path_str = str(path)
    if not path_str.startswith(MAGIC):
        # have to merge as strings since Path.joinpath doesn't do the trick
        path = Path(MAGIC + path_str)

    return path


def magic_resolve(path: Path) -> Path:
    """
    Adds magic Windows prefix and resolves symlinks.
    """
    return magic(path.resolve())


def fix_perms(path: Path, activity_func: Callable = lambda x: None) -> None:
    """
    Fix the permissions of an individual path. Not recursive.
    """
    # logger.debug("Applying stat.S_IWUSR permission to {}".format(path))
    # fix deletion permission https://blog.nathanv.me/posts/python-permission-issue/
    activity_func(("", f"Fixing permissions for {str(path)}"))
    path.chmod(stat.S_IWUSR)


def fix_perms_recursive(path: Path, activity_func: Callable = lambda x: None) -> None:
    """
    Recursively fixes the permissions of a folder so that it can be deleted.
    """
    logger.debug(f"Fixing permissions for {path}")

    for root, dirs, files in os.walk(path):
        for i in dirs + files:
            fix_perms(Path(root, i), activity_func=activity_func)


# ======================================================================================
# Directory Junctions
# ======================================================================================


def is_junction(path: Path) -> bool:
    """
    Returns if the given path is a symlink. The builtin Path.is_symlink() doesn't
    work for directory junctions, but it can resolve them however.
    """
    if path.is_symlink():
        return True

    # see if the resolved path is the same as what we started with
    return path.resolve() != path


def mk_junction(
    src: Path, dest: Path, activity_func: Callable = lambda x: None
) -> None:
    """
    Creates a directory junction between two directories.
    """
    logger.debug(f"Creating directory junction from {str(src)} to {str(dest)}")
    activity_func(("", f"Creating directory junction from {str(src)} to {str(dest)}"))

    if dest.exists():
        if not is_junction(dest):
            raise FileExistsError(dest)

        logger.debug(f"Removing existing directory junction at {str(dest)}")
        rm_junction(dest, activity_func=activity_func)

    # TODO win32
    # create the link
    command = ["cmd", "/c", "mklink", "/J", str(magic(dest)), str(magic(src))]
    logger.debug(f"Executing: {str(command)}")
    subprocess.run(
        command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def rm_junction(path: Path, activity_func: Callable = lambda x: None) -> None:
    """
    Attempts to delete the given directory junction.
    """
    if not is_junction(path):
        return

    # this will delete only the junction and not the linked directory
    activity_func(("", f"Deleting directory junction at {str(path)}"))
    path.rmdir()


# ======================================================================================
# Move/Del
# ======================================================================================


def mv_path(src: Path, dest: Path, activity_func: Callable = lambda x: None) -> None:
    """
    Move a path object from one location to another.
    """
    logger.debug(f"Moving directory from {src} to {dest}")

    if src.resolve() == dest.resolve():
        raise ValueError("Source and destination are same location")

    # apply magic
    src = magic(src)
    dest = magic(dest)

    # remove the destination if the dest already exists
    if dest.exists():
        logger.debug(f"Deleting destination {dest}")
        rm_path(dest, activity_func=activity_func)

    # copy to the new path
    activity_func(("", f"Copying {str(src)} to {str(dest)}"))
    shutil.copytree(src, dest)
    # delete the old path
    logger.debug(f"Deleting source {src}")
    rm_path(src, activity_func=activity_func)


def rm_path(
    path: Path, first: bool = True, activity_func: Callable = lambda x: None,
) -> None:
    """
    Delete a path and fix permissions issues.
    """
    path = magic(path)

    logger.debug(f"Deleting path {path}")

    # check if it exists
    if not path.exists():
        logger.debug(f"Path {path} does not exist")
        return

    try:
        # try to delete it
        activity_func(("", f"Deleting {str(path)}"))
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=False)
        else:
            path.unlink()
    except PermissionError:
        # if there is a permission error, try to fix
        logger.info(f"Path {path} deletion failed because of PermissionError")
        if first:
            fix_perms_recursive(path, activity_func=activity_func)
            rm_path(path, first=False, activity_func=activity_func)
        else:
            raise


# ======================================================================================
# Archive
# ======================================================================================


def extract_archive(
    archive: Path, path: Path = None, activity_func: Callable = lambda x: None
) -> Path:
    """
    Extracts an archive file and returns the output path.
    """
    if path is None:
        # same path, without extensions
        path = Path.joinpath(archive.parent, archive.name.split(".", maxsplit=1)[0])

    msg = f"Extracting archive {str(archive)} ({human_readable_size(path_size(archive))}) to {str(path)}"
    activity_func(msg)
    logger.debug(msg)

    # rar archives will not work without this
    os.makedirs(path, exist_ok=True)

    try:
        # run the extraction program
        patoolib.extract_archive(
            str(archive),
            outdir=patoolib,
            # verbosity=-1,
            interactive=False,
        )

    except patoolib.util.PatoolError as e:
        logger.exception("Unable to extract archive")
        raise ExtractionError(str(e))

    return path


def create_archive(
    path: Path, archive: Path, activity_func: Callable = lambda x: None
) -> Path:
    """
    Creates an archive file and returns the new path.
    """
    uncomp_size = human_readable_size(path_size(path))

    activity_func(
        f"Creating archive {str(archive)} of {path} ({uncomp_size} uncompressed)."
        + "\n This will almost certainly take a while."
    )

    # delete the archive if it already exists,
    # as patoolib will refuse to overwrite an existing archive
    rm_path(archive, activity_func=activity_func)

    logger.debug(f"Creating archive {str(archive)}")
    # create the archive
    try:
        # this expects files/folders in a tuple
        patoolib.create_archive(
            str(archive),
            (path,),
            # verbosity=-1,
            interactive=False,
        )
    except patoolib.util.PatoolError as e:
        logger.exception("Unable to create archive")
        raise ExtractionError(str(e))

    return archive


# ======================================================================================
# Misc
# ======================================================================================


def path_size(path: Path) -> int:
    """
    Return the size in bytes of a folder, recursively.
    """
    if path.exists():
        logger.warning(f"Path {path} does not exist")
        return 0

    if path.is_dir():
        return sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, _, filenames in os.walk(path)
            for filename in filenames
        )
    else:
        return os.path.getsize(path)


def human_readable_size(size: Num, decimal_places: int = 2) -> str:
    """
    Convert number of bytes into human readable value.
    """
    # https://stackoverflow.com/a/43690506/9944427
    # logger.debug("Converting {} bytes to human readable format".format(size))
    unit = ""
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size < 1024.0 or unit == "PB":
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"
