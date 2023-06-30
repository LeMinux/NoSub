import os
import re
import requests
import time
import sys
import webbrowser
from bs4 import BeautifulSoup

BROWSER = "/usr/bin/librewolf %s"
YOUTUBE_BASE = "https://www.youtube.com/watch?v="
ID_PATTERN = r'"videoId":"(.*?)"'
DATA_PATTERN = r'"accessibilityData":{"label":"[^"]*"}}},"descriptionSnippet":'
TIME_PATTERN = r"(\d+ (?:year|month|week|day|hour|minute|second)[s]?)(?= ago)"

if len(sys.argv) != 2:
    print("Did not provide a file of youtuber home pages")
    raise SystemExit

urlList = sys.argv[1]
assert os.path.exists(urlList)

client = webbrowser.get(BROWSER)

def loadVideo(idString):
    print(f"Loading url {YOUTUBE_BASE + idString}")
    try:
        client.open(YOUTUBE_BASE + idString)
    except webbrowser.Error as e:
        print(e)

with open(urlList, "r") as urlFile:
    for url in urlFile:
        if url.find("/videos") == -1:
            url = url.replace("\n", "/videos")

        print(f"Checking the channel {url}")
        #sleep for a second to not flood with requests
        time.sleep(1)

        #get url
        response = requests.get(url)

        #skip if url could not load
        if "Not Found" in response.text:
            print("channel is not available ", url)
            continue

        if response.status_code == 404:
            print("Error 404 channel does not exist")
            continue


        soup = BeautifulSoup(response.text, "html.parser")

        #all video information is from an imported script
        info = [script.get_text() for script in soup.find_all('script')]

        keyTerm = "var ytInitialData"
        bufferSearch = len(keyTerm)
        searchScript = ""
        #search in reverse since the script is imported lower down
        for scriptValue in info[::-1]:
            #buffer the search to avoid searching the entire string
            if scriptValue[:bufferSearch].find(keyTerm) != -1:
                searchScript = scriptValue
                break

        #get desired info
        videoIds = list(dict.fromkeys(re.findall(ID_PATTERN, searchScript)))
        videoInfo = re.findall(DATA_PATTERN, searchScript)

        #get time published
        timePublished = []
        for description in videoInfo:
            timePublished.append(re.search(TIME_PATTERN, description).group(0))

        #print(timePublished)

        #determine if video is older than a day
        foundIndex = 0
        index = 0
        loadedVideo = False
        for pubTime in timePublished:
            foundIndex = re.search(r"day|days", pubTime)
            if foundIndex:
                dayTime = pubTime[foundIndex.start() - 2:foundIndex.start()]
                if "1" in dayTime:
                    loadVideo(videoIds[index])
                    loadedVideo = True
                else:
                    break
            elif re.search(r"hour|hours", pubTime):
                loadVideo(videoIds[index])
                loadedVideo = True
            elif re.search(r"second|seconds", pubTime):
                loadVideo(videoIds[index])
                loadedVideo = True
            else:
                #videos are older no need to parse
                break

            index = index + 1

        if not loadedVideo:
            print(f"Latest upload is {pubTime} ago")

        #print statement to separate output
        print()

