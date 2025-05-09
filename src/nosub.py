import requests
import webbrowser
from bs4 import BeautifulSoup
import sys
import os
import re
import argparse
import json
import time
import sqlite3
import math
from collections import namedtuple

Constant_Codes = namedtuple('_Constant_Codes', ["EXIT_SUCCESS", "EXIT_FAILURE"])
exit_codes = Constant_Codes(EXIT_SUCCESS = 0, EXIT_FAILURE = 1)

Constant_DB = namedtuple('_Constant_DB', ["V_TABLE", "R_TABLE", "DB_NAME"])
db_tables = Constant_DB(V_TABLE = "KnownVideos", R_TABLE = "KnownReleases", DB_NAME = "knowns.db")

Constant_YT = namedtuple('_Constant_YT', ["YT_BASE", "YTER_PAGE", "YT_VIDEOS", "YT_RELEASES", "YTER_LEN", "V_ID_LEN", "R_ID_LEN"])
constant_yt = Constant_YT(YT_BASE = "https://www.youtube.com/watch?v=", YTER_PAGE = "https://www.youtube.com/@", YT_VIDEOS = "videos", YT_RELEASES = "releases", YTER_LEN = 25, V_ID_LEN = 11, R_ID_LEN = 41)

Constant_Limits = namedtuple('_Constant_Max', ["VIDEO_URL_LENGTH", "RELEASE_URL_LENGTH", "HNDL_LENGTH_MAX"])
constant_limits = Constant_Limits(VIDEO_URL_LENGTH = 43, RELEASE_URL_LENGTH = 90, HNDL_LENGTH_MAX = 30)

Constant_Infs = namedtuple('_Constant_Infs', ["LOAD_TO_KNOWN","NO_LIMIT"])
constant_infs = Constant_Infs(LOAD_TO_KNOWN = math.inf, NO_LIMIT = math.inf)

verboseprint = None

#wrapper class to allow a connection to be passed by reference
#per basis so that the connection isn't global.
#It's more clean than having the connection in a list to force
#it to be mutable. I mean this is still forcing it to be mutable, but is more "clean"
class ConnectionWrapper:
    CLOSED = 0
    OPEN = 1
    def __init__(self, connection = None, status = CLOSED):
        self.connection = connection
        self.status = status

def main():
    global verboseprint
    if init() != 0:
        print("Failed to initialize database", file = sys.stderr)
        sys.exit(exit_codes.EXIT_FAILURE)

    normal_exec = False
    release_exec = False
    max_loads = constant_infs.NO_LIMIT
    time_frame = constant_infs.LOAD_TO_KNOWN

    parser = argparse.ArgumentParser(
        prog="NoSub",
        description="Load youtube videos as if were subscribed without the need for a youtube account",
    )

    #required
    parser.add_argument("-f", "--file", type=str, required=True, help="Files with a list of youtuber urls", nargs="+")

    #change default execution behavior
    parser.add_argument("-b", "--both", action="store_true", default=False, help="Specify to check videos and releases.")
    parser.add_argument("-r", "--releases", action="store_true", default=False, help="Specify to check ONLY releases")
    parser.add_argument("-t", "--time", nargs=2, help="Specify the time frame to load videos. It must be in the format of the number and then the unit such as \"1 year\"")
    parser.add_argument("-n", "--number", type=int, nargs=1, help="Specify at most how many videos at most to load per youtuber despite time frame")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="Print out extra information")
    parser.add_argument("--clear-knowns", action="store_true", default=False, help="Clear files used to store information about videos and releases")

    # parse arguments
    args = None
    try:
        args = parser.parse_args()
    except Exception as e:
        print(e, file = sys.stderr)
        sys.exit(exit_codes.EXIT_FAILURE)


    #|----------------|
    #| check required |
    #|----------------|

    valid = True
    for file in args.file:
        if checkFile(file) is False:
            valid = False

    if not valid:
        sys.exit(exit_codes.EXIT_FAILURE)

    #|----------------|
    #| check optional |
    #|----------------|

    #for user convenience
    if args.releases and args.both:
        print("Can not use both the --both (-o) and --releases (-r) options at the same time", file = sys.stderr)
        sys.exit(exit_codes.EXIT_FAILURE)

    if args.both:
        release_exec = True
        normal_exec = True
    elif args.releases:
        release_exec = True
    else:
        normal_exec = True

    if args.time:
        if args.releases:
            print("Can not specify a time frame for releases as they have no publish date", file = sys.stderr)
            sys.exit(exit_codes.EXIT_FAILURE)

        new_frame = convertToMinutes(args.time[0], args.time[1])
        if new_frame < 0:
            print("Time format given is not valid. The number must be greater than zero, and have a valid unit", file = sys.stderr)
            sys.exit(exit_codes.EXIT_FAILURE)
        time_frame = new_frame

    if args.number:
        if args.number[0] > 0:
            max_loads = args.number[0]
        else:
            print("Number must be greater than zero for --number (-n) option", file = sys.stderr)
            sys.exit(exit_codes.EXIT_FAILURE)

    verboseprint = print if args.verbose else lambda *a, **k: None

    if args.clear_knowns:
        #connection = connectToDB()
        conn_wrapped = ConnectionWrapper()
        connectToDB(conn_wrapped)
        cursor = conn_wrapped.connection.cursor()
        cursor.execute("DELETE FROM KnownVideos")
        cursor.execute("DELETE FROM KnownReleases")
        conn_wrapped.connection.commit()
        closeConnection(conn_wrapped)
        print("Cleared database")
        sys.exit(exit_codes.EXIT_SUCCESS)

    assert normal_exec or release_exec , "Uh oh how did this happen? Some how both executions are false?"

    if normal_exec and release_exec:
        normalExec(args.file, time_frame, max_loads)
        releaseExec(args.file, max_loads)
    elif normal_exec:
        normalExec(args.file, time_frame, max_loads)
    else:
        releaseExec(args.file, max_loads)

    #closeConnection()
    #end of main

def releaseExec(files, max_loads: int):
    assert files, "Not given any files"
    assert max_loads > 0, f"Max loads is not usable {max_loads=}"

    global verboseprint

    conn_wrapped = ConnectionWrapper()
    connectToDB(conn_wrapped)
    for file_name in files:
        with open(file_name, encoding = "ascii") as open_file:
            for raw_handle in open_file:
                handle = raw_handle.rstrip("\n")
                verboseprint(f"checking handle {handle}")

                releases = obtainElements(constant_yt.YT_RELEASES, handle)
                if not releases:
                    print(f"Handle \"{handle}\" does not have extractable release content", file = sys.stderr)
                    continue

                first_id = releases[0]["richItemRenderer"]["content"]["playlistRenderer"]["playlistId"]

                #if the handle has not been added then there is no known stopping point
                if not findHandle(handle, db_tables.R_TABLE, conn_wrapped):
                    if addID(handle, first_id, db_tables.R_TABLE, conn_wrapped) != 0:
                        closeConnection(conn_wrapped)
                        print("Terminating program due to malformed data", file = sys.stderr)
                        sys.exit(exit_codes.EXIT_FAILURE)

                    playlist_path = "https://www.youtube.com" + releases[0]["richItemRenderer"]["content"]["playlistRenderer"]["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
                    openPathWithBrowser(playlist_path)
                    continue #go to next url

                releases_loaded = 0
                for content in releases:
                    if releases_loaded >= max_loads:
                        break

                    playlist_id = None
                    playlist_path = None
                    try:
                        element = content["richItemRenderer"]["content"]["playlistRenderer"]
                        playlist_id = element["playlistId"]
                        playlist_path = element["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
                    except KeyError:
                        #go to next url
                        break

                    if findID(handle, playlist_id, db_tables.R_TABLE, conn_wrapped):
                        break

                    release_path = "https://www.youtube.com" + playlist_path
                    releases_loaded = releases_loaded + 1
                    openPathWithBrowser(release_path)

                    #sleep to prevent spamming
                    time.sleep(1)

                #No new releases
                if releases_loaded == 0:
                    verboseprint(f"No new releases for channel {handle}")
                elif releases_loaded > 0 and addID(handle, first_id, db_tables.R_TABLE, conn_wrapped) != 0:
                    closeConnection(conn_wrapped)
                    print("Terminating program due to malformed data", file = sys.stderr)
                    sys.exit(exit_codes.EXIT_FAILURE)
    #end of big for loop
    closeConnection(conn_wrapped)


def normalExec(files, time_frame: int, max_loads: int):
    assert files, "Not given any files"
    assert time_frame > 0, f"Time frame is not usable {time_frame=}"
    assert max_loads > 0, f"Max loads is not usable {max_loads=}"

    global verboseprint

    conn_wrapped = ConnectionWrapper()
    connectToDB(conn_wrapped)
    for file_name in files:
        with open(file_name, encoding = "ascii") as open_file:
            for raw_handle in open_file:
                handle = raw_handle.rstrip("\n")
                verboseprint(f"checking handle {handle}")

                videos = obtainElements(constant_yt.YT_VIDEOS, handle)
                if not videos:
                    print(f"Handle \"{handle}\" does not have extractable video content", file = sys.stderr)
                    continue

                first_id = videos[0]["richItemRenderer"]["content"]["videoRenderer"]["videoId"]
                offset = 0
                videos_loaded = 0

                if not findHandle(handle, db_tables.V_TABLE, conn_wrapped):
                    #if the handle has not been added then there is no known stopping point
                    if addID(handle, first_id, db_tables.V_TABLE, conn_wrapped) != 0:
                        closeConnection(conn_wrapped)
                        print("Terminating program due to malformed data", file = sys.stderr)
                        sys.exit(exit_codes.EXIT_FAILURE)

                    time_phrase = (videos[0]["richItemRenderer"]["content"]["videoRenderer"]["publishedTimeText"]["simpleText"]).split(" ")
                    converted_time = convertToMinutes(time_phrase[0], time_phrase[1])

                    if converted_time < time_frame:
                        video_path = constant_yt.YT_BASE + first_id
                        videos_loaded = videos_loaded + 1
                        openPathWithBrowser(video_path)

                        if time_frame != constant_infs.LOAD_TO_KNOWN:
                            offset = 1
                        else:
                            #go to next URL
                            continue

                #load other content
                for content in videos[offset:]:
                    if videos_loaded >= max_loads:
                        break

                    video_id = None
                    time_phrase = None
                    converted_time = None
                    try:
                        element = content["richItemRenderer"]["content"]["videoRenderer"]
                        video_id = element["videoId"]
                        time_phrase = (element["publishedTimeText"]["simpleText"]).split(" ")
                        converted_time = convertToMinutes(time_phrase[0], time_phrase[1])
                    except KeyError:
                        #have reached end of first page
                        #there is a continuation in the JSON but it doesn't show videos
                        #go to next url
                        break

                    if findID(handle, video_id, db_tables.V_TABLE, conn_wrapped):
                        break

                    #then check the time as a new video could have an id
                    #not in range
                    if converted_time > time_frame:
                        break

                    video_path = constant_yt.YT_BASE + video_id
                    videos_loaded = videos_loaded + 1
                    openPathWithBrowser(video_path)

                    #sleep to prevent spamming
                    time.sleep(1)

                #No new videos
                if offset == 0 and videos_loaded == 0:
                    time_phrase = (videos[0]["richItemRenderer"]["content"]["videoRenderer"]["publishedTimeText"]["simpleText"]).split(" ")
                    verboseprint(f"Youtube channel {handle} has not uploaded in {time_phrase[0]} {time_phrase[1]}")

                #add first id to db
                elif addID(handle, first_id, db_tables.V_TABLE, conn_wrapped) != 0:
                    closeConnection(conn_wrapped)
                    print("Terminating program due to malformed data", file = sys.stderr)
                    sys.exit(exit_codes.EXIT_FAILURE)
    #end of big for loop
    closeConnection(conn_wrapped)

def openPathWithBrowser(path: str):
    assert constant_yt.YT_BASE in path, f"Youtube URL trying to load doesn't contain the Youtube URL base {path=}"
    assert len(path) == constant_limits.VIDEO_URL_LENGTH or len(path) == constant_limits.RELEASE_URL_LENGTH, f"Path trying to load doesn't match any expected length {path=} ({len(path)})"
    verboseprint(f"Loading URL {path}")
    try:
        webbrowser.open_new_tab(path)
    except Exception as e:
        print(e)


def checkFile(file):
    assert file is not None, "Checking a None file"

    if not file or file.isspace():
        print("File given is just white space or empty", file = sys.stderr)
        return False

    if not os.path.exists(file):
        print(f"File \"{file}\" does not exist", file = sys.stderr)
        return False

    file_path = file
    if os.path.islink(file):
        file_path = os.path.realpath(file)

    if not os.path.isfile(file_path):
        print("Path given is not a file", file = sys.stderr)
        return False

    #this is here to tell the user about permissions
    #a root:root 774 would still grand readable permissions since read is set for everyone
    if not os.access(file_path, os.R_OK):
        print(f"File \"{file}\" does not have read permissions", file = sys.stderr)
        return  False


    return True

#if something like 13 months are passed in it will give the minute amount of
# 13 months. However Youtube does not do 13 months and will just say 1 year
# this then compares the time of 1 year to 13 months
# for now I will consider this user error
def convertToMinutes(number_string, unit_string):
    assert number_string is not None, "Attempting to convert None number string"
    assert unit_string is not None, "Attempting to use a None unit string"

    if not number_string.isdigit():
        return -1

    number = int(number_string)
    if number <= 0:
        return -1

    time_map = {
        r"seconds?": 1/60,
        r'minutes?': 1,
        r"hours?" : 60,
        r"days?" : 1440,
        r"weeks?" : 10080,
        r"months?": 43830,
        r"years?" : 525960,
    }

    minutes = -1
    #if there are no matches it will return -1
    for pattern, conversion in time_map.items():
        if re.search(pattern, unit_string, flags = re.IGNORECASE):
            minutes = number * conversion

    return minutes

#will not account for elements past the first scroll page
#the important thing is that only the page that gets loaded
#will have the proper contents
#loading from home (featured) will not have the same info
#as loading directly into videos or releases
def obtainElements(tab_wanted: str, handle: str):
    assert handle is not None, "Can't obtain elements from a None handle"
    assert tab_wanted in (constant_yt.YT_VIDEOS, constant_yt.YT_RELEASES), f"Invalid tab given {tab_wanted}"

    if not validateHandle(handle):
        print(f"Handle given is not a valid handle {handle}")
        return None

    #keep in mind if the tab doesn't exist it will default to the home page
    page_to_load = constant_yt.YTER_PAGE + handle + "/" + tab_wanted
    response = requests.get(page_to_load)

    if response.status_code == 404:
        print(f"Error 404: channel {handle} does not exist.", file = sys.stderr)
        return None

    soup = BeautifulSoup(response.content, "html.parser")

    #all video information is from an imported script that has ytInitialData
    info = [script.get_text() for script in soup.find_all('script')]
    keyTerm = "var ytInitialData"
    bufferSearch = 17
    searchScript = ""

    #for scriptValue in info:
    #reverse search seems to be a little faster
    for scriptValue in info[::-1]:
        #buffer the search to avoid searching the entire string
        if scriptValue[:bufferSearch].find(keyTerm) != -1:
            searchScript = scriptValue
            break

    if not searchScript:
        print("Could not find data required to load", file = sys.stderr)
        return None

    #Semicolon is going to be there most of the time, but in case it isn't
    #I don't want the last } to be removed and ruin the parser
    if searchScript[-1] == ';':
        #semi colon at the end messes up the parser
        json_data = json.loads(searchScript[searchScript.index("{"):-1])
    else:
        json_data = json.loads(searchScript[searchScript.index("{"):])

    #title in JSON has upper case
    cap_tab = tab_wanted.capitalize()
    tab_returned = None
    for tab in json_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]:
        try:
            #if the page is not loaded directly to the expected tab it will not
            #have the content field
            if tab["tabRenderer"]["title"] == cap_tab:
                tab_returned = tab["tabRenderer"]["content"]["richGridRenderer"]["contents"]
                break
        except KeyError:
            break

    #This could go through the elements and return an array with the elements
    #needed but that would be an extra loop to do work that may not be needed
    #in addition to a loop needing to parse through the returned array anyway.
    return tab_returned

def validateHandle(handle: str):
    assert handle is not None, "Passed None to validate handle"

    #a handle length of a single character can exist
    #messing around I found a channel with @e
    handle_len = len(handle)
    if handle_len > constant_limits.HNDL_LENGTH_MAX or handle_len == 0:
        return False

    white_list = r"^[a-zA-Z0-9-_.]+$"
    if not re.fullmatch(white_list, handle):
        return False

    return True

def validateVideoId(id: str):
    assert id is not None, "Passed None to validate video id"

    if len(id) != constant_yt.V_ID_LEN:
        return False

    white_list = r"^[a-zA-Z0-9-_]+$"
    if not re.fullmatch(white_list, id):
        return False

    return True

def validateReleaseId(id: str):
    assert id is not None, "Passed None to validate release id"

    if len(id) != constant_yt.R_ID_LEN:
        return False

    white_list = r"^[a-zA-Z0-9-_]+$"
    if not re.fullmatch(white_list, id):
        return False

    return True

#This will abstract away if it's updating or adding a new handle
#either way it's still adding the id
def addID(handle:str, id: str, table: str, conn_wrapper: ConnectionWrapper):
    assert id is not None, "Can't add a None id"
    assert handle is not None, "Can't add a None handle"
    assert table in (db_tables.V_TABLE, db_tables.R_TABLE), f"Invalid table given {table}"
    assert isinstance(conn_wrapper, ConnectionWrapper), "Not using the connection wrapper for adding an ID"
    assert conn_wrapper.status == conn_wrapper.OPEN, "Attempting to used a closed connection to add an ID"

    #with the usage of parameterized queries sanitization is not necessary
    #but validation is necessary to prevent garbage data in.
    #If garbage data is entered then that garbage can't be found with expected data
    if not validateHandle(handle):
        print(f"Invalid handle given \"{handle}\".", file = sys.stderr)
        return -1

    if table == db_tables.V_TABLE:
        if not validateVideoId(id):
            print(f"Invalid video id given \"{id}\".", file = sys.stderr)
            return -1
    else:
        if not validateReleaseId(id):
            print(f"Invalid playlist id given \"{id}\".", file = sys.stderr)
            return -1

    count_handle = f"SELECT COUNT(id) FROM {table} WHERE handle = ?;"
    #connection = connectToDB()
    cursor = conn_wrapper.connection.cursor()
    result = (cursor.execute(count_handle, (handle,))).fetchone()[0]
    #add entry if it doesn't exist otherwise update it
    #if it fails to add there is no need to rollback as the single statement failed
    if result == 0:
        add_query = f"INSERT INTO {table} (handle, known_id) VALUES (?, ?);"
        try:
            cursor.execute(add_query, (handle, id))
        except Exception as e:
            print(e)
            sys.exit(exit_codes.EXIT_FAILURE)
    else:
        update_query = f"UPDATE {table} SET known_id = ? WHERE handle = ?;"
        try:
            cursor.execute(update_query, (id, handle))
        except Exception as e:
            print(e)
            sys.exit(exit_codes.EXIT_FAILURE)

    conn_wrapper.connection.commit()

    return 0

#handle is needed to associate the id to something and have a reference
#back to older ids to be removed
def findID(handle: str, id: str, table: str, conn_wrapper: ConnectionWrapper):
    assert id is not None, "Can't find a None id"
    assert handle is not None, "Can't find a None handle"
    assert table in (db_tables.V_TABLE, db_tables.R_TABLE), f"Invalid table given {table}"
    assert isinstance(conn_wrapper, ConnectionWrapper), "Not using the connection wrapper for finding an ID"
    assert conn_wrapper.status == conn_wrapper.OPEN, "Attempting to used a closed connection to find an ID"

    search_query = f"SELECT COUNT(id) FROM {table} WHERE known_id = ? AND handle = ?;"
    #connection = connectToDB()
    cursor = conn_wrapper.connection.cursor()
    result = (cursor.execute(search_query, (id, handle))).fetchone()[0]
    if result == 0:
        return False
    else:
        return True

def findHandle(handle: str, table: str, conn_wrapper: ConnectionWrapper):
    assert handle is not None, "Can't find a None handle"
    assert table in (db_tables.V_TABLE, db_tables.R_TABLE), f"Invalid table given {table}"
    assert isinstance(conn_wrapper, ConnectionWrapper), "Not using the connection wrapper for finding a handle"
    assert conn_wrapper.status == conn_wrapper.OPEN, "Attempting to used a closed connection to find a handle"

    search_query = f"SELECT COUNT(id) FROM {table} WHERE handle = ?;"
    #connection = connectToDB()
    cursor = conn_wrapper.connection.cursor()
    result = (cursor.execute(search_query, (handle,))).fetchone()[0]
    if result == 0:
        return False
    else:
        return True

def connectToDB(conn_object: ConnectionWrapper):
    assert isinstance(conn_object, ConnectionWrapper), "Tried to make a connection without the wrapper"

    if conn_object.status == conn_object.CLOSED:
        conn_object.connection = sqlite3.connect(db_tables.DB_NAME, isolation_level = None)
        conn_object.status = conn_object.OPEN


    assert conn_object.status == conn_object.OPEN, "Opening a DB connection resulted in a status of closed"
    assert conn_object.connection is not None, "Connection object is opened but remained None"

def closeConnection(conn_object: ConnectionWrapper):
    assert isinstance(conn_object, ConnectionWrapper), "Tried to close a connection without the wrapper"

    if conn_object.status == conn_object.OPEN:
        conn_object.connection.close()
        conn_object.connection = None
        conn_object.status = conn_object.CLOSED

    assert conn_object.status == conn_object.CLOSED, "Closing a connection still kept the connection status open"
    assert conn_object.connection is None, "Connection object is closed but is not None"

def init():
    conn_wrapped = ConnectionWrapper()
    connectToDB(conn_wrapped)
    status = 0
    try:
        cursor = conn_wrapped.connection.cursor()
        #auto increment is used since string primary keys are a little bit
        #slower. For the videos table it isn't as bad, but the releases one
        #the unique id is 41 characters. Re-indexing would
        #be better on an int than a string
        create_videos = """
        CREATE TABLE IF NOT EXISTS KnownVideos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle varchar(30) UNIQUE NOT NULL,
            known_id varchar(11) UNIQUE NOT NULL
        );
        """
        create_releases = """
        CREATE TABLE IF NOT EXISTS KnownReleases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle varchar(30) UNIQUE NOT NULL,
            known_id varchar(41) UNIQUE NOT NULL
        );
        """
        cursor.execute(create_videos)
        cursor.execute(create_releases)
        conn_wrapped.connection.commit()
    except sqlite3.Error as error:
        print(error)
        status = -1

    closeConnection(conn_wrapped)
    return status

if __name__ == "__main__":
    main()
