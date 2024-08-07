import argparse
import cProfile
import logging.config
import logging.handlers
import pstats
import sqlite3
import os
from dotenv import load_dotenv, dotenv_values
from PIL import Image, ExifTags
import hashlib


TABLE_DEFS = [{
    "name": "media",
    "query": '''CREATE TABLE media
    (
    id INTEGER PRIMARY KEY,
    FILENAME TEXT NOT NULL,
    FILEPATH TEXT NOT NULL UNIQUE,
    HASH TEXT NOT NULL,
    FILETYPE TEXT NOT NULL,
    DATETIME TEXT NOT NULL,
    LATITUDE TEXT,
    LONGITUDE TEXT
    );
    '''
}]

try:
    load_dotenv()
except Exception as e:
    print(e)

LOGGER_NAME = "PHOTOS_MANAGER"
DB_NAME = "photos_manager.db"

parser = argparse.ArgumentParser()

def createTable(conn, table_def):
    logger.info(f'Creating table: {table_def["name"]}')
    try:    
        conn.execute(table_def["query"])
    except Exception as e:
        logger.exception(f'Failed to create table named: {e}')
        logger.debug(e)

def dropTables(conn):

    logger.info("Dropping tables...")

    for table_def in TABLE_DEFS:

        try:
            conn.execute(f"DROP TABLE {table_def['name']}")
            logger.info(f"Dropped table named: {table_def['name']}")
        except Exception as e:
            logger.exception(f"Failed to drop {table_def['name']}")
            logger.debug(e)

def checkIfTablesExists(conn):

    curr = conn.cursor()
    for table_def in TABLE_DEFS:
        name = table_def["name"]
        logger.debug(name)
        curr.execute(f"SELECT * FROM sqlite_master WHERE type='table' AND name='{name}';")
        res = curr.fetchall()
        logger.debug(res)
        if len(res) == 0:
            createTable(conn, table_def)
        else:
            logger.debug(f"Table: {table_def['name']} exists")

def setupArgparser():

    parser.add_argument("-t", "--test", help="This is only a test argument", action="store_true")
    parser.add_argument("-c", "--critical", help="Set the logger level to critical, otherwise default level is INFO", action="store_true")
    parser.add_argument("-p", "--profile", help="Run the script with the profiler turned on", action="store_true")
    parser.add_argument("-db", "--setupdb", help="Create the database and the tables for directories and mediaFiles", action="store_true")
    parser.add_argument("-ddb", "--dropdb", help="Drop all the tables in the database", action="store_true")
    # parser.add_argument("-cdb", "--checkdb", help="Check if db tables exist", action="store_true")
    parser.add_argument("-f", "--find", help="Find media within the TEST_DIR path specified in the .env file", action="store_true")
    parser.add_argument("path", type=str, nargs="?", help="Path in which to search for media. If no path is specified, the env var path 'TEST_DIR' will be used", default=os.getenv("TEST_DIR"))

    

    try:
        args = parser.parse_args()
        return args
    except Exception as e:
        print(f'Error parsing args: {e}')

def setupLogger(LEVEL):

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
                "level": LEVEL
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": LEVEL,
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

def connectToDB():

    logger.info("Connecting to database")
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

def searchForDirectories(path):

    logger.info(f"Searching {path}")

    dirCount = 0
    with os.scandir(path) as dirResults:

        for entry in dirResults:
            if not entry.name.startswith(".") and entry.is_dir():
                dirCount += 1 + searchForDirectories(entry.path)

    return dirCount

def searchForFiles(path):
    # logger.info(f"\tSearching {path}")

    files = []
    with os.scandir(path) as dirResults:

        for entry in dirResults:
            if not entry.name.startswith("."):
                if entry.is_dir():
                    files = files + searchForFiles(entry.path)
                else:
                    files.append(entry.path)

    return files

def findMedia(target_dir):
    
    logger.info(f"Looking for media in root dir: {target_dir}")
    # dirCount = searchForDirectories(target_dir)
    files = searchForFiles(target_dir)

    logger.info(f"There are {len(files)} media files contained within {target_dir}")

    return files

def insertDataIntoDB(imgData, dbConn):

    logger.info(f"Adding info for image: {imgData['filename']} to db")
    curr = dbConn.cursor()
    try:
        curr.execute(f"INSERT INTO media (FILENAME, FILEPATH, HASH, FILETYPE, DATETIME, LATITUDE, LONGITUDE) VALUES ('{imgData['filename']}', '{imgData['filepath']}', '{imgData['hash']}', '{imgData['filetype']}', '{imgData['date']}', '{imgData['lat']}', '{imgData['lon']}')")
        dbConn.commit()
    except Exception as e:
        logger.exception(f"Failed to insert data for image: {imgData['filepath']} into db")
        logger.exception(e)


def processJPG(filepath):

    img = Image.open(filepath)
    exifData = {
            ExifTags.TAGS[k]: v
            for k, v, in img._getexif().items()
            if k in ExifTags.TAGS
        }

    
    imgData = {
        "hash": "",
        "filename": filepath.split("/")[-1],
        "filetype": filepath.split(".")[-1],
        "filepath": filepath,
        "date": "",
        "lat": "",
        "lon": ""
    }

    try:
        imgData = {
            "hash": hashlib.sha256(img.tobytes()).hexdigest(),
            "filename": filepath.split("/")[-1],
            "filetype": filepath.split(".")[-1],
            "filepath": filepath,
            "date": "" if exifData.get("DateTime", None) is None else exifData["DateTime"],
            "lat": 0 if exifData.get("GPSInfo", None) is None else round(float(exifData["GPSInfo"][2][0] + exifData["GPSInfo"][2][1]/60 + exifData["GPSInfo"][2][2]/3600), 6),
            "lon": 0 if exifData.get("GPSInfo", None) is None else round(float(exifData["GPSInfo"][4][0] + exifData["GPSInfo"][4][1]/60 + exifData["GPSInfo"][4][2]/3600), 6),
        }
    except Exception as e:
        logger.exception(f"Failed to process file at path: {filepath}")
        logger.exception(e)

    return imgData

PROCESSORS = [(["jpg", "jpeg"], processJPG)]

def processMedia(files, dbConn):

    fileTypes = []
    
    # for filepath in ["test_dir/IMG_3277.JPG"]:
    for filepath in files:
        logger.info(f"Processing file: {filepath}")
        extension = filepath.split(".")[-1]

        if extension not in fileTypes:
            fileTypes.append(extension)

        for processer in PROCESSORS:

            if extension.lower() in processer[0]:
                imgData = processer[1](filepath)
                # logger.info(imgData)
                insertDataIntoDB(imgData, dbConn)



    logger.info(f"{len(fileTypes)} file types were found")
    for ext in fileTypes:
        logger.info(f"\t{ext}")

if __name__ == "__main__":

    conn = None

    with cProfile.Profile() as profile:

        args = setupArgparser()

        logger = setupLogger("CRITICAL" if args.critical else "INFO")
                

        #setup connection to DB and check to see if the proper tables exist
        conn = connectToDB()
        checkIfTablesExists(conn)
    
        if args.find:
            filepaths = findMedia(args.path)

            processMedia(filepaths, conn)    

        if args.dropdb:
            dropTables(conn)
        
        #if a connection to the db was created during execution, close the connection
        if conn:
            closeDBConnection(conn)
        else:
            logger.debug("DB connection not opened")

        if args.profile:
            results = pstats.Stats(profile)
            results.sort_stats(pstats.SortKey.TIME)
            results.print_stats()
            results.dump_stats("results.prof")


