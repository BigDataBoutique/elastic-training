#!/bin/bash

#verifying date executable
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    date_ex=date
#mac
elif [[ "$OSTYPE" == "darwin"* ]]; then
    date_ex=gdate
    if ! $date_ex &>/dev/null
    then
        echo "please install coreutils"
        exit 1
    fi
#win git-bash
elif [[ "$OSTYPE" == "msys" ]]; then
    date_ex=date
else
  date_ex=date
  if ! $date_ex &>/dev/null
  then
      echo "unknown OS"
      exit 1
  fi
fi

#looping over files
for f1 in $1/*.csv
do
    #get date from filename
    filedate=$(echo ${f1##*/} | tr -d '.csv' | tr '-' '/')
    timestamp=$($date_ex '+%Y-%m-%d' -d $filedate)

    #looping over lines
    {
    #skipping header
    read line
    #determining file type. V2 files have FIPS in the header
    if [[ $line == *FIPS* ]]; then
      type='V2'
    else
      type='V1'
    fi
    while read line
    do
      #replacing commas with |
      line2=$(echo $line | sed -Ee :1 -e 's/^(([^",]|"[^"]*")*),/\1|/;t1')
      #fixing date format
      line2=$(echo $line2 | sed -e "s/\([0-9]\) \([0-9]\)/\1T\2/g")
      #removing control characters and double quotes
      line2=$(echo $line2 | tr -d '"[:cntrl:]')
      # adding file date to data - must be at beginning because early V1 has fewer fields
      line2=$timestamp"|"$line2
      echo "{ \"Type\": \"$type\", \"Message\": \"$line2\" }"
      echo "\n"
      echo $type
      echo "\n"
      #sending to elasticsearch
      curl -XPOST 'http://localhost:9200/corona-v2-fb/_doc?pipeline=coronacsvs' -H "Content-Type: application/json" -d "{ \"Type\": \"$type\", \"Message\": \"$line2\" }"
    done
    } < $f1
    # this means the input file gets is fed into a compound command
done
