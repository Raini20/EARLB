FROM --platform=linux/amd64 python:3.12-slim

# Plots als Dateien speichern statt ein Fenster zu öffnen
ENV MPLBACKEND=Agg

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Systembibliotheken, die Open3D braucht
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libgl1 libegl1 libx11-6 libusb-1.0-0 libudev1 libgomp1 \
       libidn2-0 libcap2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work