import pytest

from rigol_cli.catalog import COMMANDS, get_command, render_command
from rigol_cli.errors import ProtocolError


def test_catalog_names_are_unique_and_cover_every_manual_section():
    assert len(COMMANDS) == len({item.name for item in COMMANDS})
    assert {
        "general", "system", "acquire", "display", "timebase", "trigger",
        "trigger-edge", "trigger-pulse", "trigger-video", "trigger-slope",
        "trigger-pattern", "trigger-duration", "trigger-alternate", "storage",
        "math", "channel", "measure", "waveform", "logic", "key", "other",
    } == {item.section for item in COMMANDS}


def test_ds1000d_only_commands_are_not_claimed_for_ds1152e():
    names = {item.name for item in COMMANDS if "DS1000E" not in item.models}
    assert names == {
        "logic.display", "logic.digital-turn", "logic.digital-position",
        "logic.threshold", "logic.position-reset", "logic.group",
        "logic.group-size", "key.logic",
    }


def test_render_templated_commands_and_validate_indices():
    variables = {"channel": 2, "digital": None, "group": None, "mode": None}
    assert render_command(get_command("channel.scale"), variables) == ":CHANnel2:SCALe"
    variables = {"channel": None, "digital": None, "group": None, "mode": "EDGE"}
    assert render_command(get_command("trigger.source"), variables) == ":TRIGger:EDGE:SOURce"
    with pytest.raises(ProtocolError, match="--channel"):
        render_command(
            get_command("channel.scale"),
            {"channel": None, "digital": None, "group": None, "mode": None},
        )


def test_trigger_templates_reject_modes_not_supported_by_the_manual():
    variables = {"channel": None, "digital": None, "group": None, "mode": "pulse"}
    assert render_command(get_command("trigger.level"), variables) == ":TRIGger:PULSE:LEVel"
    variables["mode"] = "SLOPE"
    with pytest.raises(ProtocolError, match="supports --mode"):
        render_command(get_command("trigger.level"), variables)
    variables["mode"] = "VIDEO"
    with pytest.raises(ProtocolError, match="supports --mode"):
        render_command(get_command("trigger.sweep"), variables)


def test_unknown_catalog_name_is_actionable():
    with pytest.raises(ProtocolError, match="commands list"):
        get_command("missing")
