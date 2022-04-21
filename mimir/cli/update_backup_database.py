import logging

import click

from mimir.frontend.terminal.application import initDatabase

log_format = "[%(asctime)s] %(name)-40s %(levelname)-8s %(message)s"
logging.basicConfig(
    format=log_format,
    level="INFO",
)

logger = logging.getLogger(__name__)


@click.command()
@click.argument("mimir_base")
def cli(mimir_base):
    """
    Cli script for updating the database saved in MIMIR_BASE/.mimir. Equivalent to
    running MTF and doing "missing files" and "Update paths" in database options.
    This explicitly expects that no **new** files are added when running it. Only fewer
    """

    database, status = initDatabase(mimir_base)
    logger.info("Got database at %s with status %s", database, status)
    logger.info("Checking paths")
    database.checkChangedPaths()
    logger.info("Checking missing files")
    database.checkMissingFiles(mod_id=False)
    logger.info("Resetting entry ids")
    database.reset_entry_ids()
    logger.info("Saving database")
    database.saveMain()


if __name__ == "__main__":
    cli()
