sudo docker build -t rtl_fm_transcriber .

sudo docker run --rm --privileged --device /dev/bus/usb --device /dev/snd -p 8080:8080 -it rtl_fm_transcriber