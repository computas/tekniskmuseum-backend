#!/bin/bash
categories=""
input="../dict_eng_to_nor_difficulties_v2.csv"
pattern=" |'"

# if there is a command line argument, use this as the csv-file to 
# read categories instead.
if [ $# -gt 0 ]
  then
    input=$1
fi

while IFS=',' read -ra
 line
do
  gsutil -m cp gs://quickdraw_dataset/full/simplified/"${line[0]}".ndjson ./images/"${line[0]}".ndjson
done < "$input"