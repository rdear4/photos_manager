import argparse
import cProfile
import logging.config
import logging.handlers
import pstats

parser = argparse.ArgumentParser()
# logging.basicConfig(filename="test.log", level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

def setupArgparser():
    parser.add_argument("-t", "--test", help="This is only a test argument", action="store_true")
    parser.add_argument("-p", "--profile", help="Run the script with the profiler turned on", action="store_true")

    return parser.parse_args()

def setupLogger():

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(asctime)s [%(levelname)s|%(module)s|%(lineno)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "stderr": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "stream": "ext://sys.stderr",
                "level": "WARNING"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "filename": "photos_manager.log",
                "maxBytes": 10000,
                "backupCount": 3
            }
        },
        "loggers": {
            "root": {"level": "DEBUG", "handlers": ["stderr", "file"]}
        }

    }

    logger = logging.getLogger("photos_manager")

    logging.config.dictConfig(logging_config)

    return logger

if __name__ == "__main__":

    with cProfile.Profile() as profile:

        logger = setupLogger()

        logger.debug("********************************************************")
        logger.debug("Setting up argparser..")
        args = setupArgparser()
        logger.debug("Argparser setup complete")

    if args.profile:
        results = pstats.Stats(profile)
        results.sort_stats(pstats.SortKey.TIME)
        results.print_stats()
        results.dump_stats("results.prof")
    




