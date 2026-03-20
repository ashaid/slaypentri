import pytest

try:
    from painter import check_display_environment
    import painter as _painter_module
    PAINTER_AVAILABLE = True
except ImportError:
    PAINTER_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PAINTER_AVAILABLE, reason="painter.py not yet implemented")


def test_wayland_exit(mock_wayland_env):
    """CFG-05: Pure Wayland session (WAYLAND_DISPLAY set, DISPLAY absent) must call sys.exit(1)."""
    with pytest.raises(SystemExit) as exc_info:
        check_display_environment()
    assert exc_info.value.code == 1, "Must exit with code 1 on Wayland-only"


def test_wayland_exit_message(mock_wayland_env, capsys):
    """CFG-05: Exit message must mention X11 requirement."""
    with pytest.raises(SystemExit):
        check_display_environment()
    captured = capsys.readouterr()
    assert "X11" in captured.out or "x11" in captured.out.lower(), \
        "Error message must mention X11"
    assert "DISPLAY" in captured.out, "Error message must mention DISPLAY variable"


def test_xwayland_ok(mock_xwayland_env):
    """CFG-05: XWayland session (both WAYLAND_DISPLAY and DISPLAY set) must NOT exit."""
    # Should complete without raising SystemExit
    check_display_environment()


def test_x11_ok(mock_x11_env):
    """CFG-05: Pure X11 session (only DISPLAY set) must NOT exit."""
    check_display_environment()


def test_pause_zero():
    """CFG-06: pyautogui.PAUSE must be 0.0 after painter module is imported."""
    import pyautogui
    assert pyautogui.PAUSE == 0.0, (
        f"pyautogui.PAUSE should be 0.0, got {pyautogui.PAUSE}. "
        "painter.py must set pyautogui.PAUSE = 0 at module level."
    )
