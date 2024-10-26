# SSL Neon FC

This repo contains all the main code needed to run project neon's RoboCop ssl intelligence.

## Communication between modules

The whole ssl environment is divided in several modules most of them are represented on the following diagram

![env_diagram](ssl.svg)

The following modules are maintained by the RoboCup community:
1. [SSL-Vision](https://github.com/RoboCup-SSL/ssl-vision): This program transform the camera image in robot position and field geometry
2. Auto-ref ([Tigers](https://github.com/TIGERs-Mannheim/AutoReferee) & [ER-Force](https://github.com/robotics-erlangen/autoref)): This program  filters the vision data and judges if any fault were commited
3. [Game Controller](https://github.com/RoboCup-SSL/ssl-game-controller/): This program manages the real game state by reading what the auto refs sent and the human ref decision

The following modules are maintained by our team:
1. [Neon FC](): This is the part of the code that connects all computer side software programs and makes the decision for each robot velocities.
2. [Interface](): Here all the interaction between the decision and the human user are centered
3. [Firmware](): This is the repo that contains all the embedded software robots and station

##  Running

This project is maneged using poetry and is meant to be run on ubuntu

```poetry run python neonfc_ssl/game.py```
