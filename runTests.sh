#!/bin/bash

fileFlag=false

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
	echo "Running: py.test -v --cov-report=html --cov=backend $RUNON"
	py.test -v --cov-report=html --cov=backend $RUNON
    else
	echo "Running: py.test -v $RUNON"
	py.test -v $RUNON
    fi
	
else
    echo "Argument 1 should be all or valid filename"
fi
