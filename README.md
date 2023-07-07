# Google-Reviews-Scraper

# User Guide

## 1. Create your own google API key if you don’t have one.
### a. Go to the Google Cloud Console: https://console.cloud.google.com/
### b. Sign in with the Google account you want to associate with the API key.
### c. Create a new project or select an existing project from the project dropdown in
the top navigation bar.
### d. In the sidebar, click on "APIs & Services" and then click on "Credentials."
### e. On the Credentials page, click on the "Create Credentials" button and select
"API Key" from the dropdown menu.
### f. A dialog box will appear displaying your newly created API key. Take note of
this key as it will be used to authenticate your requests to Google APIs.
### g. You can further customize the API key by restricting its usage to specific IP
addresses, HTTP referrers, or API restrictions. These settings provide an added
layer of security and control over the key's usage.
### h. Once you have created and configured the API key, make sure to securely store
it. Do not expose your API key publicly, such as in public repositories or clientside code, as it can lead to unauthorized usage and potential security issues.
### i. For more detailed instructions and information, you can refer to the official
Google Cloud documentation on creating an API key:
https://cloud.google.com/docs/authentication/gettingstarted#creating_the_api_key
### j. Replace 'Your_API_Key' with your real google API key in app.py.
## 3. Download Firefox browser and geckodriver that matches your computer.
b. Firefox Brower download page: https://www.mozilla.org/en-CA/firefox/new/
c. geckodriver download page: https://github.com/mozilla/geckodriver/releases.
Please choose the one that matches your computer, i.e. if you are using
windows 64-bit operating system, you should choose win64.zip.
4
d. You could use test_selenium.py to check if you installed a matched version. If
so when you run it, you will see it open a Firefox browser window on google (it
will be closed quickly which is expected).
e. Also set path to geckodriver as per your configuration, change it to your path
where you save the geckodriver accordingly in app.py line 257. 
