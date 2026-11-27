# MOLA-LO fuer Hilti 2022 Exp14 -- reproduzierbare Umgebung
# ROS 2 Jazzy, MOLA-LO aus den offiziellen Binaerpaketen (>= 3.3.0 enthaelt das hilti2022-Profil)
FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive
# ros-jazzy-mola-metric-maps ist zwingend, wird aber von mola-lidar-odometry NICHT als
# Abhaengigkeit gezogen: die ICP-Pipeline laedt libmola_metric_maps.so erst zur Laufzeit
# per YAML. Fehlt sie, verwirft MOLA-LO jeden Scan und endet trotzdem mit Status 0.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-jazzy-mola-lidar-odometry \
        ros-jazzy-mola-metric-maps \
        ros-jazzy-mola-input-rosbag1 \
        ros-jazzy-mola-state-estimation-smoother \
        ros-jazzy-mp2p-icp \
        python3-pip python3-numpy python3-venv \
    && rm -rf /var/lib/apt/lists/*

# evo und rosbags in ein eigenes venv. NICHT per "pip3 install --break-system-packages":
# evo zieht ein neueres numpy, und das von Debian gelieferte numpy 1.26.4 hat keine
# RECORD-Datei, laesst sich also von pip nicht deinstallieren -> Build bricht ab mit
# "Cannot uninstall numpy 1.26.4, RECORD file not found".
# Das venv liegt bewusst auf dem PATH, damit run_exp14.sh evo_* direkt findet.
RUN python3 -m venv /opt/evo \
    && /opt/evo/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/evo/bin/pip install --no-cache-dir evo rosbags
ENV PATH=/opt/evo/bin:$PATH

# Abbruch beim Build, falls das Hilti-Profil, das Metric-Maps-Plugin, die Karten-Tools
# oder evo fehlen -- lieber hier scheitern als spaeter mit einer leeren Trajektorie.
RUN . /opt/ros/jazzy/setup.sh && \
    dpkg-query -W ros-jazzy-mola-lidar-odometry && \
    (command -v mola-lo-cli-hilti2022 || find /opt/ros/jazzy -name 'mola-lo-cli-hilti2022' -print -quit | grep -q .) && \
    find /opt/ros/jazzy -name 'libmola_metric_maps.so' -print -quit | grep -q . && \
    command -v sm2mm && command -v mm2ply && \
    command -v evo_ape && evo_ape --help > /dev/null

WORKDIR /ws
SHELL ["/bin/bash", "-c"]
ENTRYPOINT ["/bin/bash", "-c", "source /opt/ros/jazzy/setup.bash && exec \"$@\"", "--"]
CMD ["bash"]
