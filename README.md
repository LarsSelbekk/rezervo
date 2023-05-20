# 🏋🏿‍♂️ sit-rezervo

[![sit-rezervo](https://img.shields.io/badge/ghcr.io-mathiazom%2Fsit--rezervo-blue?logo=docker)](https://github.com/users/mathiazom/packages/container/package/sit-rezervo)

Automatic booking of [Sit Trening group classes](https://www.sit.no/trening/gruppe)

### 🧑‍💻 Development
1. In the [`docker`](docker) directory, define `.env` and `config.json` based on [`.env.template`](sit_rezervo/.env.template) and [`config.template.json`](sit_rezervo/config.template.json). This includes defining Auth0 tenant details, credentials for Slack notifications and app-wide booking preferences.
2. With [docker](https://docs.docker.com/get-docker/) and [docker compose](https://docs.docker.com/compose/) installed, run
```shell
docker compose -f docker/docker-compose.dev.yml up -d --build
```
3. Within the container (e.g. from the Terminal tab in Docker Desktop), explore available cli commands
```shell
sit-rezervo --help
```

### 🚀 Deployment
A template for a production deployment is given in [`docker-compose.template.yml`](docker/docker-compose.template.yml), which uses the most recent [`sit-rezervo` Docker image](https://github.com/users/mathiazom/packages/container/package/sit-rezervo).