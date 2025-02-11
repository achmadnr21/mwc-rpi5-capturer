#!/bin/bash
#install opencv
sudo apt install python3-opencv
sleep 2
# Menyalin direktori ke /usr/local/bin/
sudo cp -rf mwc-capturer.py /usr/local/bin/mwc-capturer/
sleep 2
# Menyalin file service ke /etc/systemd/system/
sudo cp -f mwc-capturer.service /etc/systemd/system/
sleep 2
# Menginformasikan pengguna
echo "File dan direktori telah berhasil disalin."
echo "Enabling service"
sleep 2
sudo systemctl enable mwc-capturer.service
sudo systemctl daemon-reload
echo "Starting service"
sleep 2
sudo systemctl start mwc-capturer.service
echo "Markaswalet - Techiro :: Installed :: Service Ready!"
