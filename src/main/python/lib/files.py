from pathlib import Path

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
