"""Tests for .env discovery and diagnosis.

A half-filled .env is the most common first-run failure, and the old message
("copy .env.example to .env") was actively wrong when .env already existed.
These pin down that the diagnosis names the real problem.
"""

import os

import pytest

from deriv_bot import envfile
from deriv_bot.config import ConfigError


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    """A clean directory, with the required keys absent from the environment."""
    monkeypatch.chdir(tmp_path)
    for key in envfile.REQUIRED_KEYS:
        monkeypatch.delenv(key, raising=False)
    # Keep the package-parent candidate from matching a real repo file.
    monkeypatch.setattr(envfile, "search_paths", lambda: [str(tmp_path / ".env")])
    return tmp_path


def write_env(directory, **values):
    lines = ["# a comment", ""]
    for key, value in values.items():
        lines.append(f"{key}={value}")
    (directory / ".env").write_text("\n".join(lines) + "\n", encoding="utf-8")


class TestDiscovery:
    def test_finds_an_env_in_the_working_directory(self, workdir):
        write_env(workdir, DERIV_APP_ID="1089")
        assert envfile.find() == str(workdir / ".env")

    def test_returns_none_when_absent(self, workdir):
        assert envfile.find() is None

    def test_search_paths_are_deduplicated(self):
        paths = envfile.search_paths()
        assert len(paths) == len(set(paths))

    def test_search_paths_are_absolute(self):
        assert all(os.path.isabs(p) for p in envfile.search_paths())


class TestMisnamedFiles:
    def test_detects_the_notepad_dot_txt_trap(self, workdir):
        (workdir / ".env.txt").write_text("DERIV_APP_ID=1089\n", encoding="utf-8")
        found = envfile.find_misnamed()
        assert any(f.endswith(".env.txt") for f in found)

    def test_diagnosis_explains_the_rename(self, workdir):
        (workdir / ".env.txt").write_text("DERIV_APP_ID=1089\n", encoding="utf-8")
        text = "\n".join(envfile.diagnose())
        assert "Notepad appends .txt" in text
        assert "Rename-Item" in text

    def test_no_false_positive_when_env_exists(self, workdir):
        write_env(workdir, DERIV_APP_ID="1089")
        (workdir / ".env.txt").write_text("stale\n", encoding="utf-8")
        # .env is present, so the rename advice must not appear.
        assert "Notepad appends" not in "\n".join(envfile.diagnose())


class TestKeyLineLookup:
    def test_finds_the_line_number(self, workdir):
        write_env(workdir, DERIV_APP_ID="1089", DERIV_API_TOKEN="")
        located = envfile.read_key_line(str(workdir / ".env"), "DERIV_API_TOKEN")
        assert located is not None
        number, text = located
        assert number == 4  # comment, blank, APP_ID, TOKEN
        assert text.strip() == "DERIV_API_TOKEN="

    def test_ignores_commented_lines(self, workdir):
        (workdir / ".env").write_text(
            "# DERIV_API_TOKEN=commented_out\nDERIV_API_TOKEN=real\n", encoding="utf-8"
        )
        number, _ = envfile.read_key_line(str(workdir / ".env"), "DERIV_API_TOKEN")
        assert number == 2

    def test_missing_key_returns_none(self, workdir):
        write_env(workdir, DERIV_APP_ID="1089")
        assert envfile.read_key_line(str(workdir / ".env"), "DERIV_API_TOKEN") is None

    def test_unreadable_file_returns_none(self, workdir):
        assert envfile.read_key_line(str(workdir / "nope.env"), "DERIV_API_TOKEN") is None


class TestDiagnosis:
    def test_empty_token_is_named_as_the_problem(self, workdir, monkeypatch):
        write_env(workdir, DERIV_APP_ID="1089", DERIV_API_TOKEN="")
        monkeypatch.setenv("DERIV_APP_ID", "1089")
        monkeypatch.setenv("DERIV_API_TOKEN", "")
        text = "\n".join(envfile.diagnose())
        assert "FOUND" in text
        assert "DERIV_API_TOKEN  EMPTY" in text
        assert "this is the problem" in text

    def test_it_does_not_tell_you_to_create_an_env_that_exists(self, workdir, monkeypatch):
        # The old message did exactly this, which sent the owner in circles.
        write_env(workdir, DERIV_APP_ID="1089", DERIV_API_TOKEN="")
        monkeypatch.setenv("DERIV_API_TOKEN", "")
        text = "\n".join(envfile.diagnose())
        assert "Copy-Item .env.example" not in text

    def test_missing_env_suggests_creating_one(self, workdir):
        text = "\n".join(envfile.diagnose())
        assert "NOT FOUND" in text
        assert "Copy-Item .env.example" in text

    def test_points_at_the_offending_line(self, workdir, monkeypatch):
        write_env(workdir, DERIV_APP_ID="1089", DERIV_API_TOKEN="")
        monkeypatch.setenv("DERIV_APP_ID", "1089")  # this one is fine
        monkeypatch.setenv("DERIV_API_TOKEN", "")  # this one is the problem
        text = "\n".join(envfile.diagnose())
        assert "Line 4 of your .env" in text
        assert "DERIV_API_TOKEN=" in text

    def test_points_at_the_first_broken_key(self, workdir, monkeypatch):
        # With both missing, it names the first rather than listing everything.
        write_env(workdir, DERIV_APP_ID="", DERIV_API_TOKEN="")
        monkeypatch.setenv("DERIV_APP_ID", "")
        monkeypatch.setenv("DERIV_API_TOKEN", "")
        text = "\n".join(envfile.diagnose())
        assert "Line 3 of your .env" in text

    def test_the_token_value_is_never_printed(self, workdir, monkeypatch):
        write_env(workdir, DERIV_APP_ID="1089", DERIV_API_TOKEN="")
        monkeypatch.setenv("DERIV_API_TOKEN", "sk-super-secret-value")
        monkeypatch.setenv("DERIV_APP_ID", "1089")
        text = "\n".join(envfile.diagnose())
        assert "sk-super-secret-value" not in text
        assert "21 characters" in text  # length only

    def test_reports_missing_dotenv_package(self, workdir, monkeypatch):
        monkeypatch.setattr(envfile, "dotenv_installed", lambda: False)
        text = "\n".join(envfile.diagnose())
        assert "NOT INSTALLED" in text
        assert "pip install python-dotenv" in text

    def test_explain_includes_the_original_error(self, workdir):
        text = envfile.explain(ConfigError("DERIV_API_TOKEN is required but not set"))
        assert "DERIV_API_TOKEN is required but not set" in text
        assert "Diagnosis:" in text


class TestLoading:
    def test_returns_none_without_dotenv(self, workdir, monkeypatch):
        monkeypatch.setattr(envfile, "dotenv_installed", lambda: False)
        assert envfile.load() is None

    def test_returns_none_when_no_file(self, workdir):
        assert envfile.load() is None

    def test_loads_values_into_the_environment(self, workdir, monkeypatch):
        pytest.importorskip("dotenv")
        write_env(workdir, DERIV_APP_ID="9999", DERIV_API_TOKEN="from-file")
        assert envfile.load() == str(workdir / ".env")
        assert os.environ["DERIV_API_TOKEN"] == "from-file"

    def test_existing_environment_wins(self, workdir, monkeypatch):
        pytest.importorskip("dotenv")
        write_env(workdir, DERIV_APP_ID="1089", DERIV_API_TOKEN="from-file")
        monkeypatch.setenv("DERIV_API_TOKEN", "from-shell")
        envfile.load()
        assert os.environ["DERIV_API_TOKEN"] == "from-shell"
