from fbs_runtime.application_context.PySide2 import ApplicationContext


def get_app_version(appctxt: ApplicationContext) -> str:
    """
    Returns the version of the application.
    """
    try:
        with open(appctxt.get_resource("base.json"), "r") as fp:
            data = json.load(fp)
        return "v{}".format(data["version"])
    except Exception:
        return "v??"
