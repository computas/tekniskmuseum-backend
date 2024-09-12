#!/bin/bash
categories=""
input="dict_eng_to_nor_difficulties_v2.csv"
pattern=" |'"

if [ $# -gt 0 ]
  then
    input=$1
fi

while IFS=',' read -a line
do
    echo "${line[0]}"
    if [[ ${line[0]} =~ $pattern ]]
    then
      categories="${categories} \"${line[0]}\""
    else 
      categories="${categories} ${line[0]}"
    fi
  done < "$input"

python3 preprocessing/data_migration.py $categories