#!/bin/bash

wget http://www.regionofwaterloo.ca/opendatadownloads/Inspections.zip -O /tmp/Inspections.zip
unzip -o /tmp/Inspections.zip -d testdata

python parsefacilities.py --update 
