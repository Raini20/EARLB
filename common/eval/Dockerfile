# Gemeinsames Auswerte-Image (ohne ROS): evo für ATE/RPE, pye57/scipy für den Kartenvergleich, matplotlib für Plots.
# Bauen (aus der Repo-Wurzel):  docker build --network=host -t earlb-eval -f common/eval/Dockerfile common/eval
FROM python:3.12-slim
RUN pip install --no-cache-dir evo==1.31.1 pye57==0.4.19 numpy==2.5.5 scipy==1.18.1 plyfile==1.1.5 matplotlib==3.11.2
WORKDIR /repo
