import webbrowser
import requests
from bs4 import BeautifulSoup
import re
import sys
import os

browser = "<insert browser path> %s"
youtubeURLBase = "https://www.youtube.com/watch?v="

assert len(sys.argv) == 2
urlList = sys.argv[1]
assert os.path.exists(urlList)

idPattern = r'"videoId":"(.*?)"'

#the key distinguishing feature is how this ends specifically with }}}
#this allows the regex to be much more compact that what it could have been
titlePattern = '"title":{"runs":\[{"text":".*?"}\],"accessibility":{"accessibilityData":{"label":".*?"}}}'

client = webbrowser.get(browser)

#open the file
with open(urlList, "r") as file:
    #iterate until file end
    for url in file:
        #if the url is the homepage it will add the /videos extension
        #it is more preferable to have the home page since that is much easier
        #to manipulate
        if url.find("/videos") == -1:
            url = url.replace("\n", "/videos")
        print("Checking the channel " + url)

        #obtain the HTML code
        response = requests.get(url)
        soupString = str(BeautifulSoup(response.content, "html5lib"))

        #parse through the code to get video ID and when it was published
        #due to the nature of how the HTML code is layed out
        #the first entry of the id corresponds to the first entry of date and title
        videoIds = list(dict.fromkeys(re.findall(idPattern, soupString)))
        videoDatesAndTitle = re.findall(titlePattern, soupString)

        index = 0
        #obtain the date published
        for description in videoDatesAndTitle:
            #title length is needed since it is possible to have keywords of time
            titleLength = (description.find('"}],"accessibility"')) - (description.find('"text":"') + 8)
            years = months = weeks = days = hours = minutes = seconds = -1

            #substring of just the date info and author
            dateInfo = description[description.find('"label":"') + 9 + titleLength:]

            #finds the index of the keyword of time singular or plural
            years = dateInfo.find("years")
            if years == -1:
                years = dateInfo.find("year")

            months = dateInfo.find("months")
            if months == -1:
                months = dateInfo.find("month")

            weeks = dateInfo.find("weeks")
            if weeks == -1:
                weeks = dateInfo.find("week")

            days = dateInfo.find("days")
            if days == -1:
                days = dateInfo.find("day")

            hours = dateInfo.find("hours")
            if hours == -1:
                hours = dateInfo.find("hour")

            minutes = dateInfo.find("minutes")
            if minutes == -1:
                minutes = dateInfo.find("minute")

            seconds = dateInfo.find("seconds")
            if seconds == -1:
                seconds = dateInfo.find("second")

            #obtains the number before the time unit via regular expression
            if years != -1:
                years = int(re.search(r"\b(\d+)\s+(year|years)",dateInfo).group(1))
            if months != -1:
                months = int(re.search(r"\b(\d+)\s+(month|months)",dateInfo).group(1))
            if weeks != -1:
                weeks = int(re.search(r"\b(\d+)\s+(week|weeks)",dateInfo).group(1))
            if days != -1:
                days = int(re.search(r"\b(\d+)\s+(day|days)",dateInfo).group(1))
            if hours != -1:
                hours = int(re.search(r"\b(\d+)\s+(hour|hours)",dateInfo).group(1))
            if minutes != -1:
                minutes = int(re.search(r"\b(\d+)\s+(minute|minutes)",dateInfo).group(1))
            if seconds != -1:
                seconds = int(re.search(r"\b(\d+)\s+(second|seconds)",dateInfo).group(1))

            #only 1 day old
            if days == 1 and years == -1 and months == -1 and weeks == -1:
                try:
                    client.open(youtubeURLBase + videoIds[index])
                except webbrowser.Error as e:
                    print(e)
                    file.close()
            #less than a day old
            elif days == -1 and years == -1 and months == -1 and weeks == -1:
                try:
                    client.open(youtubeURLBase + videoIds[index]);
                except webbrowser.Error as e:
                    print(e)
                    file.close()
            else:
                #no need to continue parsing since videos will be older
                break

            index += 1

print("Finished parsing")
