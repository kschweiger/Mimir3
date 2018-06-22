#!/bin/bash
mkdir testStructure
cd testStructure
touch rootFile1.mp4
mkdir folder1 folder2
cd folder1
touch folder1file1.mp4
touch folder1file2.mp4
cd ../folder2
touch folder2file1.mp4
touch folder2file2.mp4
mkdir folder3
cd folder3
touch folder3file1.mp4
cd ../../../
