#!/bin/sh
cd /home/pi/photomaton/_data/ 
rsync -avz --remove-source-files _pics/ mont-perdu:_data/_pics/
