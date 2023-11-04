import logging

import click

from mimir.frontend.terminal.application import App, initDatabase


def initLogging(thisLevel, funcLen="24"):
    log_format = "[%(asctime)s] %(name)-40s %(levelname)-8s %(message)s"
    if thisLevel == 20:
        thisLevel = logging.INFO
    elif thisLevel == 10:
        thisLevel = logging.DEBUG
    elif thisLevel == 30:
        thisLevel = logging.WARNING
    elif thisLevel == 40:
        thisLevel = logging.ERROR
    elif thisLevel == 50:
        thisLevel = logging.CRITICAL
    else:
        thisLevel = logging.NOTSET

    logging.basicConfig(
        format=log_format,
        level=thisLevel,
        # TODO: Send to file
        filename="myapp.log",
        filemode="w"
        # datefmt="%H:%M:%S"
    )


def run(baseDir, config=None, autofind=True):
    database, status = initDatabase(baseDir, config)
    logging.info("Got database at %s with status %s", database, status)
    logging.info("Starting application")
    app = App(database)
    app.start()


@click.command()
@click.option("--folder", help="Base folder containing the data", required=True)
@click.option(
    "--config",
    help="MTF config file",
    default=None,
    show_default=True,
)
@click.option(
    "--log-level",
    help="Define logging level: CRITICAL - 50, ERROR - 40, WARNING - 30, INFO - 20,"
    " DEBUG - 10, NOTSET - 0. Set to 0 to activate ROOT root messages",
    type=int,
    default=20,
    show_default=True,
)
@click.option(
    "--auto-find",
    is_flag=True,
    show_default=True,
    default=True,
    help="Will disable to automatically executed file earch in root dir",
)
def main(folder: str, config: None | str, log_level: int, auto_find: bool):
    initLogging(log_level)
    if folder.endswith("/"):
        folder = folder[:-1]
    run(baseDir=folder, config=config, autofind=auto_find)


if __name__ == "__main__":
    main()
