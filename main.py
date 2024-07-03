import argparse
import cProfile
import logging.config
import logging.handlers
import pstats
import sqlite3

LOGGER_NAME = "PHOTOS_MANAGER"
DB_NAME = "photos_manager.db"

parser = argparse.ArgumentParser()
# logging.basicConfig(filename="test.log", level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

def setupArgparser():
    
    logger.debug("Setting up argparser..")

    parser.add_argument("-t", "--test", help="This is only a test argument", action="store_true")
    parser.add_argument("-p", "--profile", help="Run the script with the profiler turned on", action="store_true")
    parser.add_argument("-db", "--setupdb", help="Create the database and the tables for directories and mediaFiles", action="store_true")
    parser.add_argument("-ddb", "--dropdb", help="Drop all the tables in the database", action="store_true")

    

    try:
        args = parser.parse_args()
        logger.debug("Attempted to parse args")
        logger.debug("Argparser setup complete")
        return args
    except Exception as e:
        logger.exception(f'Error parsing args: {e}')

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
                "stream": "ext://sys.stdout",
                "level": "DEBUG"
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

    logger = logging.getLogger(LOGGER_NAME)

    logging.config.dictConfig(logging_config)

    return logger

def createDirectoriesTable(conn):
    pass

def setupDatabase():

    logger.debug("Connecting to database")
    connection = None

    try:
        connection = sqlite3.connect(DB_NAME)
    except Exception as e:
        logger.exception("Unable to connect to the database")


    # logger.debug("Creating directories table")
    return connection

def closeDBConnection(conn):
    logger.debug("Closing connection to db")

    try:
        conn.close()
        logger.debug("DB connection closed")
    except Exception as e:
        logger.exception(f'Unable to close the connection to the db: {e}')

if __name__ == "__main__":

    conn = None

    with cProfile.Profile() as profile:

        logger = setupLogger()

        logger.debug("********************************************************")
        args = setupArgparser()        

        if args.setupdb:

            conn = setupDatabase()
            

    if args.profile:
        results = pstats.Stats(profile)
        results.sort_stats(pstats.SortKey.TIME)
        results.print_stats()
        results.dump_stats("results.prof")
    
    if conn:
        closeDBConnection(conn)
    else:
        logger.debug("DB connection not opened")



