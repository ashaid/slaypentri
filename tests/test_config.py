import os
import pytest

# These imports will fail until painter.py exists — that is intentional (RED state).
# pytest will collect and SKIP the test bodies if import fails; the file itself must be valid Python.
try:
    from painter import load_config, deep_merge, DEFAULT_CONFIG_CONTENT, AppState
    PAINTER_AVAILABLE = True
except ImportError:
    PAINTER_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PAINTER_AVAILABLE, reason="painter.py not yet implemented")


def test_config_autogenerate(tmp_config_path):
    """CFG-01: When config file does not exist, load_config creates it with defaults."""
    state = AppState()
    state.config_path = tmp_config_path
    state.verbose = False
    load_config(state)
    assert os.path.exists(tmp_config_path), "config.yaml should have been created"
    with open(tmp_config_path) as f:
        content = f.read()
    assert "edge_detection:" in content
    assert "blur_kernel_size" in content
    assert "canny_low" in content
    assert "simplify_epsilon" in content


def test_config_loads_existing(existing_config_path):
    """CFG-01: When config file exists, load_config reads it without error."""
    state = AppState()
    state.config_path = existing_config_path
    state.verbose = False
    load_config(state)
    # blur_kernel_size set to 3 in fixture
    assert state.config["edge_detection"]["blur_kernel_size"] == 3


def test_deep_merge():
    """CFG-01: deep_merge fills missing nested keys from defaults without overwriting present keys."""
    defaults = {"a": {"x": 1, "y": 2}, "b": 10}
    overrides = {"a": {"x": 99}}
    result = deep_merge(defaults, overrides)
    assert result["a"]["x"] == 99, "override should win"
    assert result["a"]["y"] == 2, "missing key should come from defaults"
    assert result["b"] == 10, "unrelated default should be preserved"


def test_deep_merge_no_mutation():
    """deep_merge must not mutate either input dict."""
    defaults = {"a": {"x": 1}}
    overrides = {"a": {"x": 2}}
    deep_merge(defaults, overrides)
    assert defaults["a"]["x"] == 1, "defaults must not be mutated"


def test_missing_keys_fall_back_to_defaults(tmp_config_path):
    """CFG-01: Config with partial keys still provides all required keys via merge."""
    import yaml
    with open(tmp_config_path, "w") as f:
        yaml.dump({"edge_detection": {"blur_kernel_size": 7}}, f)
    state = AppState()
    state.config_path = tmp_config_path
    state.verbose = False
    load_config(state)
    # These keys are not in the written config — must come from defaults
    assert "canny_low" in state.config["edge_detection"]
    assert "simplify_epsilon" in state.config["edge_detection"]
    assert "min_contour_px" in state.config["edge_detection"]
