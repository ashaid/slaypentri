import os
import textwrap
import numpy as np
import pytest


@pytest.fixture
def tmp_config_path(tmp_path):
    """Returns a path to a config file location that does NOT exist yet (for auto-gen tests)."""
    return str(tmp_path / "config.yaml")


@pytest.fixture
def existing_config_path(tmp_path):
    """Returns a path to a minimal config.yaml that already exists."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(textwrap.dedent("""\
        edge_detection:
          blur_kernel_size: 3
    """))
    return str(cfg)


@pytest.fixture
def sample_png(tmp_path):
    """Creates a small 64x64 grayscale PNG with a white square on black background."""
    import cv2
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    img[10:50, 10:50] = 255  # white square
    path = str(tmp_path / "test_image.png")
    cv2.imwrite(path, img)
    return path


@pytest.fixture
def blank_png(tmp_path):
    """Creates a 64x64 all-black PNG (produces zero contours)."""
    import cv2
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    path = str(tmp_path / "blank.png")
    cv2.imwrite(path, img)
    return path


@pytest.fixture
def mock_wayland_env(monkeypatch):
    """Sets WAYLAND_DISPLAY without DISPLAY — pure Wayland session."""
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.delenv("DISPLAY", raising=False)


@pytest.fixture
def mock_xwayland_env(monkeypatch):
    """Sets both WAYLAND_DISPLAY and DISPLAY — XWayland session."""
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("DISPLAY", ":0")


@pytest.fixture
def mock_x11_env(monkeypatch):
    """Sets only DISPLAY — pure X11 session."""
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")
