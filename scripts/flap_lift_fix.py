import os
import re
import sys

TAG = ";FLAPFIX"


def fix_coeff(line: str, undo: bool = False) -> str:
    # parse value from the config file and divide it by 2, and reassemble
    regex = r"(\S+\s*=\s*)(\d*\.?\d+)(.*$)"

    groups = list(re.findall(regex, line)[0])
    coeff = float(groups[1])
    if undo:
        new_coeff = str(coeff * 2)
    else:
        new_coeff = str(coeff / 2)
    groups[1] = new_coeff

    return "".join(groups + ["\n"])


def fix_lift_coef_flaps(file_contents: list, undo: bool = False) -> list:
    # fix lift_coef_flaps value
    for i, line in enumerate(file_contents):
        if line.startswith("lift_coef_flaps"):
            file_contents[i] = fix_coeff(line, undo=undo)

    return file_contents


def fix_lift_scalar(file_contents: list, undo: bool = False) -> list:
    # fix lift_scalar values under the FLAPS sections
    for i, line in enumerate(file_contents):
        if line.startswith("lift_scalar"):
            file_contents[i] = fix_coeff(line, undo=undo)

    return file_contents


def remove_tag(file_contents: list) -> list:
    # remove fixed tag from file line list
    new_contents = []

    for line in file_contents:
        if TAG not in line:
            new_contents.append(line)

    return new_contents


def add_tag(file_contents: list) -> list:
    # add fixed tag to file line list
    file_contents.insert(0, TAG + "\n")
    return file_contents


def check_tag(file_contents: list) -> list:
    # check for existing fixed tag in file line list
    return any(TAG in line for line in file_contents)


def fix_flight_model(filename: str, undo: bool = False) -> None:
    print("Fixing: {}".format(filename))

    with open(filename, "r+") as fp:
        # read the data in
        flight_model_content = fp.readlines()

        # check for tag if we're fixing
        if check_tag(flight_model_content) and not undo:
            print("{} already fixed. Skipping...".format(filename))
            return

        # check for tag if we're undoing
        if not check_tag(flight_model_content) and undo:
            print("{} already undone. Skipping...".format(filename))
            return

        # new_flight_model_content = fix_lift_coef_flaps(flight_model_content,undo=undo)
        new_flight_model_content = fix_lift_scalar(flight_model_content, undo=undo)

        if undo:
            new_flight_model_content = remove_tag(new_flight_model_content)
        else:
            new_flight_model_content = add_tag(new_flight_model_content)

        # write it back out
        fp.seek(0)
        fp.writelines(new_flight_model_content)
        fp.truncate()


def main() -> None:
    flight_models = []

    undo = "--undo" in sys.argv

    with open("files.txt", "r") as fp:
        flight_models = fp.readlines()

    app_data = os.getenv("APPDATA")

    for flight_model in flight_models:
        # strip new line
        flight_model = flight_model.strip()
        # substitute app data
        flight_model = flight_model.replace("%APPDATA%", app_data)

        if not os.path.isfile(flight_model):
            print("{} is not a real file!".format(flight_model))
            continue

        fix_flight_model(flight_model, undo=undo)


if __name__ == "__main__":
    main()
