# SR-LIVO – Ubuntu 20.04, ROS Noetic, PCL 1.10, Ceres 1.14, OpenCV 4.2
# Build (aus systems/sr_livo/):  docker build -t sr_livo -f docker/Dockerfile .
FROM ros:noetic-perception-focal

ARG SR_LIVO_COMMIT=97a26660ca0d3723e1556b447d3b7d34f2866555
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        git build-essential cmake \
        libceres-dev libeigen3-dev libpcl-dev libopencv-dev \
        ros-noetic-pcl-ros ros-noetic-cv-bridge ros-noetic-image-transport \
        ros-noetic-rviz ros-noetic-tf \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Auswertung (evo) im selben Container. Bewusst VOR Patches/Build: so bleibt diese Schicht im Cache und
# eine Patch-Änderung löst keinen erneuten Download aus. Lange Timeouts/Retries für langsame Leitungen.
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --default-timeout=120 --retries 10 -r /tmp/requirements.txt

# Livox-SDK + livox_ros_driver (nur zum Bauen von SR-LIVO nötig, kein Livox-Sensor im Einsatz)
RUN git clone --depth 1 https://github.com/Livox-SDK/Livox-SDK.git /opt/Livox-SDK \
    && cd /opt/Livox-SDK/build && cmake .. && make -j"$(nproc)" && make install

WORKDIR /catkin_ws/src
RUN git clone --depth 1 https://github.com/Livox-SDK/livox_ros_driver.git \
    && git clone https://github.com/ZikangYuan/sr_livo.git \
    && cd sr_livo && git checkout ${SR_LIVO_COMMIT}

# Eigene Patches auf SR-LIVO (siehe patches/*.patch, Begründung im Patch-Kopf)
COPY patches/ /tmp/patches/
RUN cd /catkin_ws/src/sr_livo && for p in /tmp/patches/*.patch; do echo "apply $p" && git apply -v "$p"; done

# Parallele Jobs nach freiem RAM: jede SR-LIVO-Datei braucht beim Kompilieren 1.5-3 GB (PCL/Ceres/Eigen).
# BUILD_JOBS=auto -> 1 Job je 2.5 GB MemAvailable der WSL-VM, höchstens nproc
# (Laptop, WSL ~6.6 GB: 2 Jobs; PC mit 64 GB, WSL ~32 GB: ~12 Jobs).
# Mit -j$(nproc) auf dem Laptop lief WSL in den Swap. Fester Wert: --build-arg BUILD_JOBS=<n>
ARG BUILD_JOBS=auto
WORKDIR /catkin_ws
RUN J="${BUILD_JOBS}"; \
    if [ "$J" = auto ]; then \
        J=$(awk '/MemAvailable/ {print int($2 / 2500000)}' /proc/meminfo); \
        [ "$J" -gt "$(nproc)" ] && J=$(nproc); \
        [ "$J" -lt 1 ] && J=1; \
    fi; \
    echo "catkin_make mit -j$J (BUILD_JOBS=${BUILD_JOBS})"; \
    /bin/bash -c "source /opt/ros/noetic/setup.bash && catkin_make -DCMAKE_BUILD_TYPE=Release -j$J"

RUN echo "source /opt/ros/noetic/setup.bash" >> /root/.bashrc \
    && echo "source /catkin_ws/devel/setup.bash" >> /root/.bashrc

WORKDIR /work/sr_livo
CMD ["bash"]
