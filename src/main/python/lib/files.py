import shutil
import subprocess
from pathlib import Path
from typing import Union

from loguru import logger

Num = Union[float, int]

# https://stackoverflow.com/a/50924863
# this is truly voodoo magic
MAGIC = "\\\\?\\"


def add_magic(path: Path) -> Path:
    """
    Adds magic Windows prefix that allows support of paths longer than 256 characters.
    """
    path_str = str(path)
    if not path_str.startswith(MAGIC):
        path = Path.joinpath(Path(MAGIC), path)

    return path


def fix(path: Path) -> Path:
    """
    Adds magic Windows prefix and resolves symlinks.
    """
    path = add_magic(path)
    return path.resolve()


def is_junction(path: Path) -> bool:
    """
    Returns if the given path is a symlink. The builtin Path.is_symlink() doesn't
    work for directory junctions, but it can resolve them however.
    """
    if path.is_symlink():
        return True

    # see if the resolved path is the same as what we started with
    return not path.resolve().samefile(path)


def create_junction(src: Path, dest: Path) -> None:
    """
    Creates a directory junction between two directories.
    """
    logger.debug(f"{src}, {dest}")
    if dest.exists():
        if is_junction(dest):
            # works fine in removing the junction but not
            # the source directory
            dest.rmdir()
        else:
            raise FileExistsError(dest)

    # create the link
    # TODO win32
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(add_magic(dest)), str(add_magic(src))],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def move_dir(src: Path, dest: Path) -> None:
    """
    Move a path object from one location to another.
    """
    shutil.move(str(add_magic(src)), str(add_magic(dest)))


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
