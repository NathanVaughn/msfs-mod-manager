import argparse
import os
import pkgutil
import shutil
import subprocess

import patoolib.programs
import PySide6

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT_DIR)


def main(console: bool) -> None:
    # clean build dir
    build_dir = os.path.join(ROOT_DIR, "build")
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)

    # clean dist dir
    dist_dir = os.path.join(ROOT_DIR, "dist")
    if os.path.isdir(dist_dir):
        shutil.rmtree(dist_dir)

    # build directories
    pyside6_dir = os.path.abspath(os.path.dirname(PySide6.__file__))
    patool_programs = [
        m.name for m in list(pkgutil.iter_modules(patoolib.programs.__path__))
    ]

    # build command
    cmd = [
        "poetry",
        "run",
        "pyinstaller",
        "app.py",
        "--clean",
        "--noconfirm",
        "--onedir",
        "--name=MSFSModManager",
        f"--add-data={os.path.join(ROOT_DIR, 'app','assets')};assets",
        f"--add-data={os.path.join(pyside6_dir, 'plugins')};plugins",
        f"--add-data={os.path.join(pyside6_dir, 'translations')};translations",
        f"--add-data={os.path.join(pyside6_dir, 'qt.conf')};.",
        f"--icon={os.path.join(ROOT_DIR, 'app','assets','icon.ico')}",
    ] + [
        f"--hiddenimport=patoolib.programs.{patool_program}"
        for patool_program in patool_programs
    ]

    if console:
        cmd.append("--console")
    else:
        cmd.append("--noconsole")

    print(f"Executing: {' '.join(cmd)}")
    subprocess.check_call(cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--console", action="store_true")
    args = parser.parse_args()

    main(args.console)
