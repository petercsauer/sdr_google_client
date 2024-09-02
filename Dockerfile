# Use a Python base image suitable for Raspberry Pi
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    rtl-sdr \
    sox \
    portaudio19-dev \
    gcc \
    libasound-dev \
    alsa-utils \
    cmake \
    git \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your script into the container
COPY client.py .

# Copy Google Cloud credentials
COPY credentials.json /root/.google/credentials.json
ENV GOOGLE_APPLICATION_CREDENTIALS="/root/.google/credentials.json"

# Command to run the script
# Command to run rtl_fm and pipe output to the Python script
CMD ["bash", "-c", "rtl_fm -f 162.400M -M fm -s 24k -r 24k -g 35 - | tee >(aplay -D hw:2,0 -t raw -f S16_LE -r 24000 -c 1) | sox -t raw -r 24000 -e signed-integer -b 16 -c 1 - -t wav - | python3 client.py"]
