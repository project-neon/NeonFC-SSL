# NeonFC-SSL Developer Guide

## Requirements:
- python 3.12
- poetry
- docker
- SSL-Vision (physical only)
- VNC Client

## Installation

### Install a VNC Client
Some distros already comes with a VNC Client, like Remmina (Ubuntu) or Connections (Fedora).
If yours don't have one, you can choose the option you like best.

### Ensure that your python version is 3.12.x:

```bash
python -V # or python3 -V
```

If you have a different version install 3.12 through pyenv.
You can reference the [pyenv installation guide](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation)

### Install poetry in your device:

Follow the [poetry installation section](https://python-poetry.org/docs/#installing-with-pipx)

### In the NeonFC-SSL directory configure the project by running:

```bash
poetry install
```

### Install Docker **Engine** (you can also install Desktop for a gui)

- Follow the [guide for your linux distro](https://docs.docker.com/engine/install/)
- Follow the [post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/) to be able to run docker commands without `sudo`
- Install [docker compose](https://docs.docker.com/compose/install/linux/#install-using-the-repository)

### Install SSL-Vision (physical only):

Use the [guide](https://github.com/RoboCup-SSL/ssl-vision) provided by the category. Be sure that you have all the dependecies packages installed.

## Running

### Start docker containers

Before anything, you will need to add a permission to docker show the application's gui.
This can be done by running the following command:

```bash
xhost +local:docker > /dev/null
```

This always needs to run before the autoref container runs.

You can avoid having to run this everytime by adding this command to your Shell RC file.
If you have the default shell, add the command to the end of the `.bashrc` file.
You can do this through:

```bash
echo 'xhost +local:docker > /dev/null' >> ~/.bashrc
```

Now you can start running the containers.
There are two ways, by using compose or by running both images separately.

#### With compose
```bash
docker compose up # at the project's base path
```

#### Separately (needs two separate terminals)
```bash
# First term (grSim)
docker run --net=host -eVNC_PASSWORD=vnc -eVNC_GEOMETRY=1920x1080 robocupssl/grsim vnc
```

```bash
# Second term (auto-ref)
docker run --net host -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=unix$DISPLAY tigersmannheim/auto-referee-vnc
```

### grSim configuration

In your VNC Client enter the following address: localhost:5900, choose VNC as the connection type.
When starting the connection a password will be requested, input "vnc"

After connecting to the container, you already face grSim, you will need to make a couple of adjustments:
1. Under Geometry > Game > Division, change to "Division B" in the dropdown
2. Under Geometry > Game > Robot Count, change to 6
3. Under Communication > Vision multicast port, change to 10006

After this changes you should be able to see the robots displayed in the auto-ref field.

### Running the code
In the project's base path, run:

```bash
poetry run neonfc
```

**Done!**

## Known errors and solutions
-- Complete here --
