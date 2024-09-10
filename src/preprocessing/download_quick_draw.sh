#!/bin/bash
input="../dict_eng_to_nor_difficulties_v2.csv"
while IFS=',' read -ra
 line
do
  gsutil -m cp gs://quickdraw_dataset/full/simplified/"${line[0]}".ndjson ./images/"$line".ndjson
  echo "$line"
done < "$input"