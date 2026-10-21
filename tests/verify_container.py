"""Build/run evidence checks used after docker build in CI."""

import os
from pathlib import Path
import subprocess
import sys

from PIL import Image
import zxingcpp


def command(*args):
    completed = subprocess.run(args, text=True, capture_output=True, check=True)
    print("$ " + " ".join(args), flush=True)
    print(completed.stdout, end="", flush=True)
    print(completed.stderr, end="", file=sys.stderr, flush=True)
    return completed.stdout.strip()


def verify(image):
    uid = command("docker", "run", "--rm", "--entrypoint", "id", image, "-u")
    assert uid == "10001", f"Expected non-root UID 10001, received {uid}"
    output = Path("container-output").resolve()
    output.mkdir(exist_ok=True)
    # Bind-mount ownership comes from the host; give this test's non-root UID access.
    if os.name != "nt":
        os.chmod(output, 0o777)
    name = "qr-generator-ci"
    command("docker", "run", "-d", "--name", name, "--network", "none", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--mount", f"type=bind,source={output},target=/app/qr_codes", "-e", "QR_CODE_DIR=qr_codes/custom", "-e", "FILL_COLOR=black", "-e", "BACK_COLOR=white", image, "--url", "https://www.njit.edu")
    status = command("docker", "wait", name)
    logs = command("docker", "logs", name)
    assert status == "0", f"Container exited {status}"
    assert "QR code successfully saved to /app/qr_codes/custom/" in logs
    command("docker", "inspect", "--format", "Status={{.State.Status}} ExitCode={{.State.ExitCode}} User={{.Config.User}}", name)
    files = list((output / "custom").glob("*.png"))
    assert len(files) == 1
    with Image.open(files[0]) as code:
        decoded = zxingcpp.read_barcode(code)
        assert decoded is not None and decoded.text == "https://www.njit.edu"
    print("PASS: non-root user, successful logs, command override, environment variables, bind mount, and decoded QR URL.", flush=True)
    default = command("docker", "run", "--rm", "--network", "none", image)
    assert "QR code successfully saved" in default
    command("docker", "rm", name)


if __name__ == "__main__":
    verify(sys.argv[1])
