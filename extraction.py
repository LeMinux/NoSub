import argparse
import requests
import os
import sys
import json
from bs4 import BeautifulSoup
from collections import namedtuple

Constant_Codes = namedtuple('_Constant_Codes', ["EXIT_SUCCESS", "EXIT_FAILURE"])
exit_codes = Constant_Codes(EXIT_SUCCESS = 0, EXIT_FAILURE = 1)

Constant_YT = namedtuple('_Constant_YT', ["YTER_PAGE", "YT_VIDEOS", "YT_RELEASES"])
constant_yt = Constant_YT(YTER_PAGE = "https://www.youtube.com/@", YT_VIDEOS = "/videos", YT_RELEASES = "/releases")

def main():
    parser = argparse.ArgumentParser(
        prog="Youtube Page Extractor",
        description="Utility program to extract the data returned by a youtuber's homepage",
    )

    parser.add_argument("file", type=str, help="File containing a list of urls separated by newlines to extract", nargs=1)

    args = None
    try:
        args = parser.parse_args()
    except Exception as e:
        print(e, file = sys.stderr)
        sys.exit(exit_codes.EXIT_FAILURE)

    if not os.path.isfile(args.file[0]):
        print(f"File {args.file[0]} does not exist", file = sys.stderr)

    sys.exit(exit_codes.EXIT_FAILURE)

    with open(args.file[0], "r") as url_file:
        for raw_line in url_file.read():
            split_line = raw_line.split(",")
            if len(split_line) != 2:
                print(f"Line {raw_line} needs the url and the desired base file name separated by a comma", file = sys.stderr)
                sys.exit(exit_codes.EXIT_FAILURE)

            url = split_line[0].strip()
            if constant_yt.YTER_PAGE not in url:
                print(f"URL {url} should be a youtuber's page which has the @", file = sys.stderr)
                sys.exit(exit_codes.EXIT_FAILURE)

            base_file_name = split_line[1].strip()
            html_file = base_file_name + ".html"
            #json_file = base_file_name + ".json"

            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            with open(html_file, "w") as file:
                file.write(str(soup))

            """
            if response.status_code == 404:
                continue

            info = [script.get_text() for script in soup.find_all('script')]
            keyTerm = "var ytInitialData"
            bufferSearch = 17
            searchScript = ""

            for scriptValue in info[::-1]:
                if scriptValue[:bufferSearch].find(keyTerm) != -1:
                    searchScript = scriptValue
                    break

            if not searchScript:
                print("Could not find data required to load", file = sys.stderr)
                return None

            if searchScript[-1] == ';':
                json_data = json.loads(searchScript[searchScript.index("{"):-1])
            else:
                json_data = json.loads(searchScript[searchScript.index("{"):])

            tab_returned = None
            tab = None
            if constant_yt.YT_VIDEOS in url:
                tab = "Videos"
            elif constant_yt.YT_RELEASES in url:
                tab = "Releases"

            if tab:
                for tab in json_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]:
                    try:
                        #if the page is not loaded directly to the expected tab it will not
                        #have the content field
                        if tab["tabRenderer"]["title"] == tab:
                            tab_returned = tab["tabRenderer"]["content"]["richGridRenderer"]["contents"]
                            break
                    except KeyError:
                        break

                if tab:
                    with open(json_file, "w") as file:
                        json.dump(tab_returned, file, indent=4)
                else:
                    print(f"No tab for {tab} for the url {url}")
                """


if __name__ == "__main__":
    main()
