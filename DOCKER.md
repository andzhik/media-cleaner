# Docker

Images are published to GitHub Container Registry (GHCR) at `ghcr.io/<owner>/<repo>`.

## Build triggers

| Event | Build | Push to GHCR |
|---|---|---|
| PR opened/updated | yes | no |
| PR merged to `main` | yes | yes (`main` + `sha-*` tags) |
| Version tag (`v*.*.*`) | yes | yes (semver tags) |

## Pulling an image

```bash
docker pull ghcr.io/<owner>/<repo>:main
```
