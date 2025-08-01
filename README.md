# SSL Neon FC

This repo contains the initial version of all the main code needed to run Project Neon's RoboCop SSL intelligence.

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

## Installation
This project is managed using poetry, so you need to install it first. You can follow the instructions on the [poetry website](https://python-poetry.org/docs/#installation).

It runs on python 3.12. We recommend using pyenv for managing your python versions.
```bash
poetry install
```

##  Running
To run the Neon FC, using the default config you can use the following command:
```bash
poetry run neonfc
```

If you want to specify a different config file, you can use the `--profile` option:
```bash
poetry run neonfc --profile path/to/config.toml
```

## Development
To start the full development environment, you can make the docket compose setup and run:
```bash
docker compose up
```

### Testing

Currently, the only obligatory test is layers integration tests. We haven't setup any CI pipeline to check it, so you need to run it manually and add the results to your PR.
```bash
poetry run pytest -m integration
```

Additionally, you can run the following linters/static analysers:
```bash
poetry run mypy . # For checking types
poetry run flake8 # For checking code style
```