from loguru import logger

from lib.config import config
from lib.flightsim import flightsim


def main() -> None:
    # prepare the logger
    logger.add(
        config.LOG_FILE,
        rotation="1 MB",
        retention="1 week",
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )
    logger.info("---------------------")
    logger.info("Launching application")

    flightsim.find_installation()
    for mod in flightsim.get_disabled_mods():
        print(mod.name)
        if mod.name == "test":
            mod.enable()


if __name__ == "__main__":
    main()
