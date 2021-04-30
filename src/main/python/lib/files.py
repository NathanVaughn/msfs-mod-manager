import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Union

from loguru import logger

Num = Union[float, int]

# https://stackoverflow.com/a/50924863
# this is truly voodoo magic
MAGIC = "\\\\?\\"

# ======================================================================================
# Magic
# ======================================================================================


def magic(path: Path) -> Path:
    """
    Adds magic Windows prefix that allows support of paths longer than 256 characters.
    """
    path_str = str(path)
    if not path_str.startswith(MAGIC):
        path = Path.joinpath(Path(MAGIC), path)

    return path


def magic_resolve(path: Path) -> Path:
    """
    Adds magic Windows prefix and resolves symlinks.
    """
    path = magic(path)
    return path.resolve()


def fix_perms(path: Path) -> None:
    """
    Fix the permissions of an individual path. Not recursive.
    """
    # logger.debug("Applying stat.S_IWUSR permission to {}".format(path))
    # fix deletion permission https://blog.nathanv.me/posts/python-permission-issue/
    path.chmod(stat.S_IWUSR)


def fix_perms_recursive(path: Path) -> None:
    """
    Recursively fixes the permissions of a folder so that it can be deleted.
    """

    logger.debug(f"Fixing permissions for {path}")

    for root, dirs, files in os.walk(path):
        for i in dirs + files:
            fix_perms(Path(root).joinpath(i))


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
    return not path.resolve().samefile(path)


def mk_junction(src: Path, dest: Path) -> None:
    """
    Creates a directory junction between two directories.
    """
    logger.debug(f"Creating directory junction from {src} to {dest}")

    if dest.exists():
        if not is_junction(dest):
            raise FileExistsError(dest)

        # works fine in removing the junction but not
        # the source directory
        logger.debug(f"Removing existing directory junction at {dest}")
        dest.rmdir()

    # TODO win32
    # create the link
    command = ["cmd", "/c", "mklink", "/J", str(magic(dest)), str(magic(src))]
    logger.debug(f"Executing: {str(command)}")
    subprocess.run(
        command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def rm_junction(path: Path) -> None:
    """
    Attempts to delete the given directory junction.
    """
    if not is_junction(path):
        return

    # this will delete only the junction and not the linked directory
    path.rmdir()


# ======================================================================================
# Move/Del
# ======================================================================================


def mv_path(src: Path, dest: Path) -> None:
    """
    Move a path object from one location to another.
    """
    logger.debug(f"Moving directory from {src} to {dest}")

    # apply magic
    src = magic(src)
    dest = magic(dest)

    # remove the destination if the dest already exists
    if dest.exists():
        rm_path(dest)

    # copy to the new path
    shutil.copytree(src, dest)
    # delete the old path
    rm_path(src)


def rm_path(path: Path, first: bool = True) -> None:
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
        shutil.rmtree(path, ignore_errors=False)
    except PermissionError:
        # if there is a permission error, try to fix
        logger.info(f"Path {path} deletion failed because of PermissionError")
        if first:
            fix_perms_recursive(path)
            rm_path(path, first=False)
        else:
            raise


# ======================================================================================
# Misc
# ======================================================================================


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
