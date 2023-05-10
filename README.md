# NoSub
A python program that loads the most recent video from a youtube channel without needing to sign in to a google account.

## Usage
```python3 NoSub.py <file with youtube homepages>```

  The passed in file should contain a list of youtuber's home pages I.E. https://www.youtube.com/@MrBeast (it has @ with the youtuber's tag) 
  
  You will also need to change the browser variable in accordance to webbrowser.get(<browser>). The path to the browser executable should work, but the browser name can also work.
  
  -> https://docs.python.org/3/library/webbrowser.html#webbrowser.get
  
  -> https://stackoverflow.com/questions/47118598/python-how-to-open-default-browser-using-webbrowser-module
