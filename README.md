# NAME
  NoSub

# SYNOPSIS
  python3 nosub.py [OPTION...] [FILE...]
  
# DESCRIPTION
  Python program that I made so that I don't have to login to Youtube to look at notifications for recent uploads. No need to explicity make an account to explicitly subscribe.
  Could be used for some privacy, but that depends on your browser and how it's configured and other factors.

  The default behavior of the program, as in when the user simply passes in files such as `NoSub.py file_of_tubers.txt`, is to go through the lines of the youtuber handles and load
  videos up until it finds a known id from a previous execution. If it's a fresh start or a handle that has not been seen before, as in the youtuber's handle is not in the
  database, the default behavior is to load the first video. This is done because there is no known stopping point. To change this behavior a time frame can be given
  which will lead to the program going out to find videos within the frame. However, this behavior only works on videos and not releases as releases do not have a time when they were published.

  Regardless of what ever options are used, the first new video or release id seen will be added to the database even if the given constraints specified does not cause it to explicity load.
  An example is giving a time frame of 4 days with the time option, and one of your creators has uploaded a new video different to what is seen in the database that was 7 days ago. In this
  case this new video will not be loaded, but this new video uploaded 7 days ago will be added to the database for future reference.
  
# REQUIRED OPTIONS
  **-f [FILE...], --file [FILE...]**
   
  A file or list of files written as a standard text file (ASCII) containing youtuber handles separated by newlines. There should be no https://www.youtube.com/@ or the included tab after the handle.
  An example of the tab after the handle is "shorts" in this url https://www.youtube.com/@smartereveryday/shorts. 
    
  Example of a good list:
  
    MrBeast
    sandristas009
    smartereveryday

# OPTIONAL OPTIONS
  **-b, --both**
  
  Attempt to load any new videos and releases with the given constraints.
  
  **-r, --releases**
    
  Only load new releases.
  Releases are not affected by the time option and attempting to use the time option with the releases option will
  result in a program termination.
    
  **-t [NUM] [UNIT], --time [NUM] [UNIT]**
  
  Specify a constraint of time in where if a video was uploaded before the time frame it will load.
  Videos that are uploaded after the given time frame will not be loaded.
  For Example if you said -t 14 days it would load anything before or at 14 days. A caveat on how youtube
  displays time is that there is no such thing as 1 month and 5 days. This would just be 1 month. So do not
  do something like 367 days as this would require videos to be 2 years old to even update the time.

  This option also changes the behavior of when a handle has not been known yet. The default behavior is to load only the first video,
  but when specifying this option it'll try to load more videos that fall within the time frame as the program has been given a stopping point.
  
  It takes two arguments, the first is any positive number greater than zero and the second is a specified unit of time.
  
  Valid units:
    
     second(s)
     minute(s)
     hour(s) 
     day(s)
     week(s)
     month(s)
     year(s)

  you don't need to be grammatically correct. `-t 7 day` or `-t 1 weeks` is fine.
    
  **-n, --number**
    
  Specify a constraint on how much max to load per youtuber. Something like -n 2 would load a maximum of 2 videos or releases per youtuber.
    
  **-v, --verbose**
  
  Provide verbose output such as what handle the program is at, what url is going to be loaded, and when the last youtube upload was.
    
  **--clear-knowns**
  
  Clears the database that stores what the most recent known id is. This will then reset the database back to a fresh state.

  
  ## Side note
    
  This uses Beautiful Soup, so this is susceptible to breakage if Youtube changes the HTML structure
