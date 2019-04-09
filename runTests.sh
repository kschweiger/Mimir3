#!/bin/bash

fileFlag=false

echo "Removing present .mimir file in testStructure"
rm -rf tests/testStructure/.mimir

if [ "$1" != "all" ]
then
    TESTSCRIPTS="$(ls tests/test_*.py)"
    for SCRIPT in $TESTSCRIPTS ; do
	if [ $1 == $SCRIPT ]
	then
	    fileFlag=true
	fi
    done
else
    fileFlag=true
fi

if [ $fileFlag == true ]
then
    if [ "$1" == "all" ]
    then
	RUNON="tests/"
    else
	RUNON=$1
    fi
    echo $RUNON
    echo $2
    if [ "$2" == "cov" ]
    then
	echo "Running: python -m pytest -v --cov-report=html --cov=mimir $RUNON"
	python -m pytest -v --cov-report=html --cov=mimir $RUNON
    else
	echo "Running: python -m pytest -v $RUNON"
	python -m pytest -v $RUNON
    fi

else
    echo "Argument 1 should be all or valid filename"
fi
