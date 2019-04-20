#!/bin/bash
PID=$(ps -c | grep 'VLC$'| awk '{print $1}')
if [ "${PID}" = "" ]; then
  /Applications/VLC.app/Contents/MacOS/VLC -q "${1}" &> /dev/null &
else
  kill -9 ${PID}
  /Applications/VLC.app/Contents/MacOS/VLC -q "${1}" &> /dev/null &
fi
