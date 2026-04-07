"""Tests for allowed_imports enforcement in SkillForge."""

from arise.skills.forge import _extract_imports, _check_imports, _detect_dynamic_imports


def test_extract_imports_basic():
    code = "import hashlib\nimport os\nfrom json import loads"
    result = _extract_imports(code)
    assert result == {"hashlib", "os", "json"}


def test_extract_imports_nested():
    code = "from os.path import join\nimport xml.etree.ElementTree"
    result = _extract_imports(code)
    assert result == {"os", "xml"}


def test_extract_imports_inside_function():
    code = "def foo():\n    import hashlib\n    from csv import reader\n    return 1"
    result = _extract_imports(code)
    assert result == {"hashlib", "csv"}


def test_extract_imports_empty():
    assert _extract_imports("x = 1") == set()


def test_extract_imports_syntax_error_fallback():
    code = "import hashlib\nimport os\nthis is broken {{{"
    result = _extract_imports(code)
    assert "hashlib" in result
    assert "os" in result


def test_check_imports_all_allowed():
    code = "import hashlib\nimport os"
    assert _check_imports(code, ["hashlib", "os", "json"]) == []


def test_check_imports_disallowed():
    code = "import hashlib\nimport subprocess"
    result = _check_imports(code, ["hashlib", "os"])
    assert result == ["subprocess"]


def test_check_imports_multiple_disallowed():
    code = "import subprocess\nimport socket\nimport os"
    result = _check_imports(code, ["os", "json"])
    assert result == ["socket", "subprocess"]


# --- Dynamic import detection ---

def test_detect_dunder_import():
    code = 'os = __import__("os")\nos.system("ls")'
    modules, unsafe = _detect_dynamic_imports(code)
    assert "os" in modules
    assert not unsafe


def test_detect_importlib():
    code = 'import importlib\nmod = importlib.import_module("subprocess")'
    modules, unsafe = _detect_dynamic_imports(code)
    assert "subprocess" in modules


def test_detect_exec_import():
    code = 'exec("import os")'
    _, unsafe = _detect_dynamic_imports(code)
    assert unsafe


def test_detect_eval_import():
    code = "eval(\"__import__('os').system('ls')\")"
    _, unsafe = _detect_dynamic_imports(code)
    assert unsafe


def test_check_imports_catches_dunder_import():
    code = 'x = __import__("subprocess")\nx.call(["ls"])'
    result = _check_imports(code, ["hashlib", "os"])
    assert "subprocess" in result


def test_check_imports_catches_exec_import():
    code = 'exec("import os")'
    result = _check_imports(code, ["hashlib"])
    assert "__dynamic_import__" in result


def test_check_imports_clean_with_dynamic():
    code = '__import__("hashlib")'
    result = _check_imports(code, ["hashlib"])
    assert result == []
