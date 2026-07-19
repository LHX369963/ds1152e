from contextlib import contextmanager

import pytest

import rigol_cli.cli as cli


class FakeScope:
    def __init__(self):
        self.writes = []
        self.queries = []

    def write(self, command):
        self.writes.append(command)

    def query_text(self, command, **kwargs):
        self.queries.append(command)
        if command == "*IDN?":
            return "Rigol Technologies,DS1152E,SERIAL,00.04.01.00.02"
        if "FREQuency" in command:
            return "5.000e+04"
        return "ON"


@contextmanager
def fake_session(scope):
    yield scope


def test_catalog_set_and_get_render_commands(monkeypatch, capsys):
    scope = FakeScope()
    monkeypatch.setattr(cli, "_session", lambda args: fake_session(scope))
    assert cli.main(["set", "channel.probe", "10", "--channel", "2"]) == 0
    assert scope.writes == [":CHANnel2:PROBe 10"]
    assert cli.main(["get", "channel.probe", "--channel", "2"]) == 0
    assert scope.queries[-1] == ":CHANnel2:PROBe?"
    assert capsys.readouterr().out.strip() == "ON"


def test_set_normalizes_scientific_notation_for_device_parser(monkeypatch):
    scope = FakeScope()
    monkeypatch.setattr(cli, "_session", lambda args: fake_session(scope))
    assert cli.main(["set", "timebase.scale", "2e-06"]) == 0
    assert scope.writes == [":TIMebase:SCALe 0.000002"]


def test_set_accepts_negative_trigger_enum(monkeypatch):
    scope = FakeScope()
    monkeypatch.setattr(cli, "_session", lambda args: fake_session(scope))
    assert cli.main(["set", "trigger.pulse.mode", "-GREaterthan"]) == 0
    assert scope.writes == [":TRIGger:PULSe:MODE -GREaterthan"]


def test_acquisition_mode_uses_device_aliases(monkeypatch):
    scope = FakeScope()
    monkeypatch.setattr(cli, "_session", lambda args: fake_session(scope))
    assert cli.main(["set", "acquire.mode", "EQUAL_TIME"]) == 0
    assert scope.writes == [":TIMebase:FORMat YT", ":ACQuire:MODE ETIM"]
    scope.writes.clear()
    assert cli.main(["set", "acquire.mode", "ROLL"]) == 0
    assert scope.writes == [":TIMebase:FORMat YT", ":ACQuire:MODE ROLL"]


def test_destructive_actions_require_confirmation(capsys):
    assert cli.main(["action", "general.reset"]) == 1
    assert "repeat with --yes" in capsys.readouterr().err


def test_ds1000d_only_command_is_rejected(capsys):
    assert cli.main(["get", "logic.display"]) == 1
    assert "DS1000D-only" in capsys.readouterr().err


def test_measure_parses_numeric_response(monkeypatch, capsys):
    scope = FakeScope()
    monkeypatch.setattr(cli, "_session", lambda args: fake_session(scope))
    assert cli.main(["measure", "frequency", "--channel", "1"]) == 0
    assert capsys.readouterr().out.strip() == "50000.0"
