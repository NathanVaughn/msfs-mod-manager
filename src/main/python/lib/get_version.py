import json


def get_version(appctxt):
    try:
        with open(appctxt.get_resource("base.json"), "r") as fp:
            data = json.load(fp)
        return "v{}".format(data["version"])
    except Exception as e:
        return "v??"
