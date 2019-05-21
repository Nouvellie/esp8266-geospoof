#!/bin/bash
sudo rm -rf $(pwd)/data/jobs/wigle_api.csv
sudo rm -rf $(pwd)/data/jobs/arduino.csv
read -p "Enter alias (only text, without spaces): " jsonname
read -p "Enter lat: " lat
read -p "Enter lon: " lon
echo "run,filepath,lat,lon,radius,since,comment" >> $(pwd)/data/jobs/wigle_api.csv
echo "1,$(pwd)/${jsonname}.json,${lat},${lon},1,20180101,${jsonname}" >> $(pwd)/data/jobs/wigle_api.csv
echo "run,filepath,name,location,max_networks,rssi_min,rssi_max,channel_min,channel_max" >> $(pwd)/data/jobs/arduino.csv
echo "1,$(pwd)/${jsonname}.json,${jsonname},'${jsonname}',15,-95,-25,0,50" >> $(pwd)/data/jobs/arduino.csv
sudo chmod -R 777 $(pwd)/data/jobs/wigle_api.csv $(pwd)/data/jobs/arduino.csv
sudo rm -rf $(pwd)/arduino/${jsonname}
sudo mkdir $(pwd)/arduino/${jsonname}
sudo cp $(pwd)/arduino/demo/demo.ino $(pwd)/arduino/${jsonname}/
sudo mv $(pwd)/arduino/${jsonname}/demo.ino $(pwd)/arduino/${jsonname}/${jsonname}.ino
sudo cp $(pwd)/arduino/demo/display.h $(pwd)/arduino/${jsonname}/
sudo cp $(pwd)/arduino/demo/memory.h $(pwd)/arduino/${jsonname}/
sudo cp $(pwd)/arduino/demo/switches.h $(pwd)/arduino/${jsonname}/
sudo cp $(pwd)/arduino/demo/wifi.h $(pwd)/arduino/${jsonname}/
sudo chmod -R 777 $(pwd)/arduino/${jsonname}/