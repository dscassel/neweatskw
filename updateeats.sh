#!/bin/bash

wget http://www.regionofwaterloo.ca/opendatadownloads/Inspections.zip -O /tmp/Inspections.zip
unzip -o /tmp/Inspections.zip -d testdata

cd /home/dscassel/work/neweatskw/
python parsefacilities.py --update 
python parsefacilities.py --getrecent 1 --enqueue
