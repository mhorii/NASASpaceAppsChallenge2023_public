#!/bin/bash

# desctiption

file=${1}

sed -i -e 's/desctiption/description/g' $file
