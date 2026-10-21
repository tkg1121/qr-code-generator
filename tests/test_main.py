import importlib
import logging
from pathlib import Path
import subprocess
import sys

from PIL import Image
import pytest
import zxingcpp

import main


@pytest.mark.parametrize("url", ["https://www.njit.edu", "http://github.com/kaw393939", "https://example.com/path?q=1"])
def test_valid_urls(url):
    assert main.is_valid_url(url) is True


@pytest.mark.parametrize("url", ["", "not-a-url", "example.com", "https://"])
def test_invalid_urls(url, caplog):
    assert main.is_valid_url(url) is False
    assert "Invalid URL" in caplog.text


def test_directory_creation(tmp_path):
    path = tmp_path / "nested" / "qr_codes"
    main.create_directory(path)
    main.create_directory(path)
    assert path.is_dir()


def test_directory_error_is_logged(tmp_path, caplog):
    blocked = tmp_path / "file"
    blocked.write_text("existing file", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main.create_directory(blocked / "nested")
    assert error.value.code == 1
    assert "Failed to create directory" in caplog.text


@pytest.mark.parametrize("fill, back", [("red", "white"), ("black", "white"), ("navy", "yellow")])
def test_qr_output_encodes_url_and_uses_colors(tmp_path, fill, back, caplog):
    path = tmp_path / "code.png"
    url = "https://www.njit.edu"
    with caplog.at_level(logging.INFO):
        main.generate_qr_code(url, path, fill, back)
    with Image.open(path) as image:
        assert image.format == "PNG"
        assert image.width == image.height
        result = zxingcpp.read_barcode(image)
        assert result is not None and result.text == url
        from PIL import ImageColor
        colors = set(image.convert("RGB").get_flattened_data())
        assert colors == {ImageColor.getrgb(fill), ImageColor.getrgb(back)}
    assert "successfully saved" in caplog.text


def test_invalid_url_does_not_create_output(tmp_path, caplog):
    path = tmp_path / "bad.png"
    main.generate_qr_code("invalid", path)
    assert not path.exists()
    assert "Invalid URL" in caplog.text


@pytest.mark.parametrize("failure", ["color", "directory"])
def test_generation_failure_is_logged(tmp_path, failure, caplog):
    path = tmp_path / "out.png"
    if failure == "directory":
        path = tmp_path / "missing" / "out.png"
        fill = "black"
    else:
        fill = "not-a-color"
    main.generate_qr_code("https://www.njit.edu", path, fill)
    assert "An error occurred" in caplog.text


def test_environment_configuration(monkeypatch):
    with monkeypatch.context() as context:
        context.setenv("QR_CODE_DIR", "custom")
        context.setenv("FILL_COLOR", "black")
        context.setenv("BACK_COLOR", "yellow")
        importlib.reload(main)
        assert (main.QR_DIRECTORY, main.FILL_COLOR, main.BACK_COLOR) == ("custom", "black", "yellow")
    importlib.reload(main)


@pytest.mark.parametrize("args, expected", [([], "https://github.com/kaw393939"), (["--url", "https://www.njit.edu"], "https://www.njit.edu")])
def test_cli_creates_decodable_image(tmp_path, args, expected):
    completed = subprocess.run([sys.executable, str(Path(main.__file__).resolve()), *args], cwd=tmp_path, text=True, capture_output=True, check=True)
    assert "QR code successfully saved" in completed.stdout
    images = list((tmp_path / "qr_codes").glob("QRCode_*.png"))
    assert len(images) == 1
    with Image.open(images[0]) as image:
        assert zxingcpp.read_barcode(image).text == expected
