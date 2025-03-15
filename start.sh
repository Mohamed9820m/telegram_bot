#!/bin/bash

# Install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -x google-chrome-stable_current_amd64.deb chrome
rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver
CHROMEDRIVER_VERSION=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
rm chromedriver_linux64.zip

# Set Chrome and ChromeDriver paths
export CHROME_PATH=$(pwd)/chrome/opt/google/chrome/chrome
export CHROMEDRIVER_PATH=$(pwd)/chromedriver

# Run the script
python testing.py