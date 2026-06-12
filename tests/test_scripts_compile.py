import py_compile

from validate_workspace import REQUIRED_SCRIPTS


def test_core_scripts_compile():
    for path in REQUIRED_SCRIPTS:
        assert path.exists(), f"missing script: {path}"
        py_compile.compile(str(path), doraise=True)
