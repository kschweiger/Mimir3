import argparse
import logging
from mimir.frontend.terminal.application import App, initDatabase

def initLogging(thisLevel, funcLen = "12"):
    log_format = ('[%(asctime)s] %(funcName)-'+str(funcLen)+'s %(levelname)-8s %(message)s')
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
        #TODO: Send to file
        filename='myapp.log',
        filemode='w'
        #datefmt="%H:%M:%S"
    )

def run(baseDir, config=None, autofind=True):
    database, status = initDatabase(baseDir, config)
    logging.info("Got database at %s with status %s", database, status)
    logging.info("Starting application")
    app = App(database)
    app.start()



if __name__ == "__main__":
    argumentparser = argparse.ArgumentParser(
        description='Mimir Terminal Frontend'
    )
    argumentparser.add_argument(
        "--logging",
        action = "store",
        help = "Define logging level: CRITICAL - 50, ERROR - 40, WARNING - 30, INFO - 20, DEBUG - 10, NOTSET - 0 \nSet to 0 to activate ROOT root messages",
        type=int,
        #choice=[10,20,30,40,50,0],
        default=10
    )
    argumentparser.add_argument(
        "--folder",
        action = "store",
        help = "config file",
        type = str,
        required = True
    )
    argumentparser.add_argument(
        "--config",
        action = "store",
        help = "config file",
        type = str,
        default = None
    )
    argumentparser.add_argument(
        "--disableAutoFind",
        action = "store_true",
        help = "Will disable to automatically executed file earch in root dir",
    )
    args = argumentparser.parse_args()
    initLogging(args.logging)
    run(baseDir = args.folder,
        config = args.config,
        autofind = (not args.disableAutoFind))
