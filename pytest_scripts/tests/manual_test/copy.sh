#!/bin/sh
times=$1
for ((i=1; i<=times; i++))
do
cat many_files.txt >> many_files_$i.txt
done
