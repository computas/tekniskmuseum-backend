#!/bin/bash
categories=""
input="dict_eng_to_nor_difficulties_v2.csv"
pattern=" |'"

# if there is a command line argument, use this as the csv-file to 
# read categories instead.
if [ $# -gt 0 ]
  then
    input=$1
fi

while IFS=',' read -a line
do
    if [[ ${line[0]} =~ $pattern ]]
    then
      categories="${categories} \"${line[0]}\""
    else 
      categories="${categories} ${line[0]}"
    fi
  done < "$input"



python3 customvision/upload.py $categories