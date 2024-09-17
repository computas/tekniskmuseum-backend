#!/bin/bash
input="dict_eng_to_nor_difficulties_v2.csv"
pattern=" |'"

# if there is a command line argument, use this as the csv-file to 
# read categories instead.
if [ $# -gt 0 ]
  then
    input=$1
fi

categories_arr=()

while IFS=',' read -a line
do
    categories_arr+=( "${line[0]}" )
  done < "$input"


python3 customvision/upload.py "${categories_arr[@]}"