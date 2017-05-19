#!/bin/sh
cd /home/pi/dev/paulla.paullaroid/ 
rsync -avz --remove-source-files _pics/ pyconfr2016:/home/daguerre/_data/_pics_idees2016/ 
