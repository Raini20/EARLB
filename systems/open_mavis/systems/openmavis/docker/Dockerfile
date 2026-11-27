# OpenMAVIS für den EARLB-Vergleich (Hilti 2022, Exp14)
# Ubuntu 20.04 + ROS Noetic (nur für die Bag-Konvertierung), Pangolin v0.6, OpenMAVIS auf festem Commit.
# Bauen (aus systems/openmavis/):  docker build -t openmavis -f docker/Dockerfile .
# oder über VS Code: "Dev Containers: Reopen in Container" (.devcontainer/devcontainer.json)
FROM osrf/ros:noetic-desktop

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
      build-essential cmake git wget \
      libeigen3-dev libopencv-dev libboost-all-dev libssl-dev \
      libglew-dev libgl1-mesa-dev libegl1-mesa-dev libxkbcommon-dev \
      python3-pip python3-numpy python3-yaml python3-opencv \
      ros-noetic-cv-bridge ros-noetic-rosbag \
    && rm -rf /var/lib/apt/lists/*

# Pangolin v0.6 (mit ORB-SLAM3 erprobt)
RUN git clone --branch v0.6 --depth 1 https://github.com/stevenlovegrove/Pangolin.git /opt/Pangolin \
 && cd /opt/Pangolin && mkdir build && cd build \
 && cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_EXAMPLES=OFF -DBUILD_TESTS=OFF -DBUILD_PANGOLIN_FFMPEG=OFF \
 && make -j4 && make install && ldconfig

# OpenMAVIS, fester Commit (in run.md dokumentiert)
#  - OpenCV: Ubuntu 20.04 hat 4.2, das Repo verlangt 4.4; ORB-SLAM3 baut mit 4.2 problemlos
#  - make -j ohne Grenze läuft in Docker oft aus dem RAM -> -j4
#  - Patch 0001: OPENMAVIS_VIEWER=0 startet ohne Pangolin-Fenster
ARG OPENMAVIS_COMMIT=b13b1c20e84efa4bb63564e26308541af70d03f2
COPY patches/ /opt/patches/
RUN git clone https://github.com/Byson-source/OpenMAVIS.git /opt/OpenMAVIS \
 && cd /opt/OpenMAVIS && git checkout "$OPENMAVIS_COMMIT" \
 && git apply /opt/patches/0001-optional-viewer.patch \
 && sed -i 's/find_package(OpenCV 4.4)/find_package(OpenCV 4 REQUIRED)/' CMakeLists.txt \
 && sed -i 's/^make -j$/make -j4/' build.sh \
 && chmod +x build.sh && ./build.sh \
 && echo "$OPENMAVIS_COMMIT" > /opt/OpenMAVIS/COMMIT

# rosbag -> EuRoC (aus der OpenMAVIS-README), fester Commit
ARG EUROC_TOOLS_COMMIT=41fd2c0b691b558961bea4162597a8a599e8a47e
RUN git clone https://github.com/1fwang/euroc_dataset_tools.git /opt/euroc_dataset_tools \
 && cd /opt/euroc_dataset_tools && git checkout "$EUROC_TOOLS_COMMIT"

# Repo ist gemountet und gehört einem anderen Nutzer -> sonst verweigert git den Zugriff (für run.md)
RUN git config --global --add safe.directory '*' \
 && echo "source /opt/ros/noetic/setup.bash" >> /root/.bashrc

WORKDIR /repo/systems/openmavis
