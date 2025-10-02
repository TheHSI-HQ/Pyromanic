<div align="center">

# :fire: Pyromanic :fire:

![BETA](https://img.shields.io/badge/⚠️_BETA-orange)
![Developed in Python 3.11](https://img.shields.io/badge/Developed_in-Python_>=3.11-blue?logo=python&color=blue&logoColor=white)
![Made with Flask](https://img.shields.io/badge/Made_with-Flask-blue?color=orange&logo=flask&logoColor=white)

![Supports MySQL](https://img.shields.io/badge/Supports-MySQL-green?color=greeen&logo=mysql&logoColor=white)
![Supports PostgreSQL](https://img.shields.io/badge/Supports-PostgreSQL-green?color=greeen&logo=postgresql&logoColor=white)
![Supports SQLite](https://img.shields.io/badge/Supports-SQLite-green?color=greeen&logo=sqlite&logoColor=white)

> The Quick Authentication Reverse Proxy

[Website](https://thehsi.cloud/pyromanic/) — [Documentation](https://github.com/TheHSI-HQ/Pyromanic/wiki)

</div>

## Overview

Pyromanic is a quick and simple Reverse Proxy with Authentication

## Running Pyromanic

1. Create a new Directory

```bash
mkdir pyromanic
cd pyromanic
```

2. Download the `docker-compose.yaml` from the GitHub Repo

```bash
wget https://raw.githubusercontent.com/TheHSI-HQ/Pyromanic/refs/heads/master/docker-compose.yaml
```

<details>

<summary>File Content</summary>

```yaml
services:
  pyromanic:
    image: thehsi/pyromanic:latest # alt: ghcr.io/TheHSI-HQ/pyromanic
    restart: unless-stopped
    network: host # Recommended
    # ports:
    #  - "0.0.0.0:443:443"
    #  - "0.0.0.0:80:80" # Only use if you add a Proxy infront of Pyromanic
    volumes:
      - ./config:/app/config
      # - ./assets:/app/assets # Not needed but useful for logs, databases or metrics
```

</details>

3. Create a Config Directory:

```bash
mkdir config
cd config
```

4. Download the Config files from the GitHub Repo

```bash
wget https://raw.githubusercontent.com/TheHSI-HQ/Pyromanic/refs/heads/master/config/pyromanic.yaml
wget https://raw.githubusercontent.com/TheHSI-HQ/Pyromanic/refs/heads/master/config/secrets.yaml
```

5. Edit the Config Files

```bash
nano pyromanic.yaml
nano secrets.yaml
```

6. Create the Network and Start the Compose Stack

```bash
docker compose up -d
```

7. Start using Pyromanic by going to

```url
https://<server-ip>
```
