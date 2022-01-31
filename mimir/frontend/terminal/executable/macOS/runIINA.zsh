#!/bin/zsh
PID=$(ps -c | grep 'IINA$'| awk '{print $1}')
if [ "${PID}" = "" ]; then
    /Applications/IINA.app/Contents/MacOS/iina-cli ${1}
else
    kill -9 ${PID}
    /Applications/IINA.app/Contents/MacOS/iina-cli ${1}
fi
