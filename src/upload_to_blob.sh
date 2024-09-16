#!/bin/bash
categories=""
input="dict_eng_to_nor_difficulties_v2.csv"
pattern=" |'"
num_img=50

# Process the arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --categories) 
            input="$2"
            shift # shift past the argument's value
            ;;
        --num_images)
            num_img="$2"
            shift # shift past the argument's value
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
    shift # shift past the option
done


while IFS=',' read -a line
do
    if [[ ${line[0]} =~ $pattern ]]
    then
      categories="${categories} \"${line[0]}\""
    else 
      categories="${categories} ${line[0]}"
    fi
  done < "$input"

python3 preprocessing/data_migration.py $categories -n $num_img