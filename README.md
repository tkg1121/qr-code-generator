# QR Code Generator

My IS 601 Module 7 Docker project. The app generates a timestamped PNG for a URL,
prints a log message, and exits. It runs as a non-root user inside the container.

## Source

`main.py` is the instructor's provided application, copied unchanged from
[kaw393939/module7_is601](https://github.com/kaw393939/module7_is601/blob/dffd5d1dae6ad68182a65ed6abe232a92cf10872/main.py).
The Docker setup and tests are included here. Dependencies are pinned to newer
releases compatible with Python 3.12. The base image uses the slim Bookworm
variant of the official Python image.

## Build and run

Install Docker and start its Linux engine. Then run these commands from the
project directory:

```bash
docker --version
docker build -t qr-code-generator-app .
docker run -d --name qr-generator qr-code-generator-app
docker wait qr-generator
docker logs qr-generator
docker inspect --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}} User={{.Config.User}}' qr-generator
```

The default URL is `http://github.com/kaw393939`. A successful run prints
`QR code successfully saved to /app/qr_codes/QRCode_<timestamp>.png` and exits
with status 0. This is a batch application, so `Exited (0)` is expected.
It does not need a port mapping or network access to create the QR image.

Copy the image out before removing the container:

```bash
docker cp qr-generator:/app/qr_codes ./qr_codes
docker rm qr-generator
```

## Custom URL and persistent output

In Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force qr_codes | Out-Null
docker run --rm --mount "type=bind,source=$((Get-Location).Path)\qr_codes,target=/app/qr_codes" qr-code-generator-app --url https://www.njit.edu
```

On Linux or macOS:

```bash
mkdir -p qr_codes
docker run --rm --user "$(id -u):$(id -g)" --mount "type=bind,source=$(pwd)/qr_codes,target=/app/qr_codes" qr-code-generator-app --url https://www.njit.edu
```

The image's default user is `myuser` with UID 10001. On Linux, a bind-mounted
folder keeps its host permissions; the non-root container user must have write
access. The example selects your host UID for this run. This avoids changing
host directory ownership. Docker named volumes also work with the default UID:

```bash
docker run --rm --mount type=volume,source=qr-output,target=/app/qr_codes qr-code-generator-app --url https://www.njit.edu
```

## Configuration

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `QR_CODE_DIR` | `qr_codes` | Output directory, relative to `/app` unless absolute |
| `FILL_COLOR` | `red` | QR foreground color |
| `BACK_COLOR` | `white` | QR background color |

For example:

```bash
docker run --rm -e QR_CODE_DIR=qr_codes/custom -e FILL_COLOR=black -e BACK_COLOR=white qr-code-generator-app --url https://www.njit.edu
```

Copy `.env.example` to `.env` to use `docker run --env-file .env ...`. Real `.env`
files are excluded from Git and the build context. The script supports dotenv
when run directly on the host as well.

The original script validates URL syntax and reports invalid URLs, colors, or
write failures in its logs. Some generation errors still exit with status 0,
so the automated container check verifies both the logs and a decodable PNG.
Logging goes to standard output; `docker logs` reads it. The `logs` directory
is available, but the supplied script does not write log files there.

## Image setup

- A slim official Python image provides the runtime.
- Dependencies are installed before copying source so that layer can be cached.
- The application runs as UID 10001 rather than root.
- Application source stays owned by root, and the output directories belong to
  `myuser`.
- `.dockerignore` includes only the Dockerfile, requirements, and application.
- Tests, credentials, screenshots, virtual environments, and generated output
  are not included in the image.
- `ENTRYPOINT` starts the script; `CMD` supplies the default URL and can be
  overridden with `--url`.

For stricter runtime isolation, this app also works with `--network none`,
`--cap-drop ALL`, and `--security-opt no-new-privileges`.

## Tests and GitHub Actions

```bash
python -m venv .venv
```

Activate `.venv` using `.\.venv\Scripts\Activate.ps1` on Windows or
`source .venv/bin/activate` on Linux/macOS. Then run:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

Tests validate URLs, colors, directory creation, error logs, environment
configuration, and CLI output. QR images are decoded to verify their URLs.

On every push and pull request, GitHub Actions runs the tests, builds the image,
then checks the real container's UID, logs, exit code, custom URL, environment
variables, and bind-mounted output. It also runs the default command. The tested
image and generated QR image are available as a seven-day workflow artifact.

To run the same container checks locally with Docker running:

```bash
python tests/verify_container.py qr-code-generator-app
```

## Publish to DockerHub

Sign in to DockerHub using your own account, then tag and push the tested image:

```bash
docker login
docker tag qr-code-generator-app YOUR_DOCKERHUB_USERNAME/qr-code-generator-app:latest
docker push YOUR_DOCKERHUB_USERNAME/qr-code-generator-app:latest
```

The image page will be `https://hub.docker.com/r/YOUR_DOCKERHUB_USERNAME/qr-code-generator-app`
after a successful push. Do not put passwords or access tokens in this repository.
