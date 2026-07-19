from __future__ import annotations

from dataclasses import dataclass

from .errors import ProtocolError


@dataclass(frozen=True)
class CommandSpec:
    name: str
    command: str
    kind: str
    section: str
    parameters: str = ""
    models: tuple[str, ...] = ("DS1000E", "DS1000D")
    description: str = ""
    modes: tuple[str, ...] = ()

    @property
    def can_query(self) -> bool:
        return self.kind in {"query", "query-set"}

    @property
    def can_write(self) -> bool:
        return self.kind in {"action", "set", "query-set"}


def _s(
    name: str,
    command: str,
    kind: str,
    section: str,
    parameters: str = "",
    *,
    models: tuple[str, ...] = ("DS1000E", "DS1000D"),
    description: str = "",
    modes: tuple[str, ...] = (),
) -> CommandSpec:
    return CommandSpec(name, command, kind, section, parameters, models, description, modes)


COMMANDS: tuple[CommandSpec, ...] = (
    _s("general.idn", "*IDN", "query", "general", description="Instrument identity"),
    _s("general.reset", "*RST", "action", "general", description="Reset system parameters"),
    _s("system.run", ":RUN", "action", "system"),
    _s("system.stop", ":STOP", "action", "system"),
    _s("system.auto", ":AUTO", "action", "system"),
    _s("system.hardcopy", ":HARDcopy", "action", "system", description="Save a bitmap to a USB drive attached to the scope"),
    _s("acquire.type", ":ACQuire:TYPE", "query-set", "acquire", "NORMal|AVERage|PEAKdetect"),
    _s("acquire.mode", ":ACQuire:MODE", "query-set", "acquire", "REAL_TIME|EQUAL_TIME|ROLL"),
    _s("acquire.averages", ":ACQuire:AVERages", "query-set", "acquire", "2|4|8|16|32|64|128|256"),
    _s("acquire.sample-rate", ":ACQuire:SAMPlingrate", "query", "acquire", "CHANnel1|CHANnel2|DIGITAL"),
    _s("acquire.memory-depth", ":ACQuire:MEMDepth", "query-set", "acquire", "NORMal|LONG"),
    _s("display.type", ":DISPlay:TYPE", "query-set", "display", "VECTors|DOTS"),
    _s("display.grid", ":DISPlay:GRID", "query-set", "display", "FULL|HALF|NONE"),
    _s("display.persist", ":DISPlay:PERSist", "query-set", "display", "ON|OFF"),
    _s("display.menu-time", ":DISPlay:MNUDisplay", "query-set", "display", "1|2|5|10|20|INFinite"),
    _s("display.menu-status", ":DISPlay:MNUStatus", "query-set", "display", "ON|OFF"),
    _s("display.clear", ":DISPlay:CLEar", "action", "display"),
    _s("display.brightness", ":DISPlay:BRIGhtness", "query-set", "display", "0..32"),
    _s("display.intensity", ":DISPlay:INTensity", "query-set", "display", "0..32"),
    _s("timebase.mode", ":TIMebase:MODE", "query-set", "timebase", "MAIN|DELayed"),
    _s("timebase.offset", ":TIMebase:OFFSet", "query-set", "timebase", "seconds"),
    _s("timebase.delayed-offset", ":TIMebase:DELayed:OFFSet", "query-set", "timebase", "seconds"),
    _s("timebase.scale", ":TIMebase:SCALe", "query-set", "timebase", "seconds/div"),
    _s("timebase.delayed-scale", ":TIMebase:DELayed:SCALe", "query-set", "timebase", "seconds/div"),
    _s("timebase.format", ":TIMebase:FORMat", "query-set", "timebase", "YT|XY|ROLL"),
    _s("trigger.mode", ":TRIGger:MODE", "query-set", "trigger", "EDGE|PULSe|VIDEO|SLOPe|PATTern|DURation|ALTernation"),
    _s("trigger.source", ":TRIGger:{mode}:SOURce", "query-set", "trigger", "CHANnel1|CHANnel2|EXT|EXT5|AC_LINE", modes=("EDGE", "PULSE", "VIDEO", "SLOPE")),
    _s("trigger.level", ":TRIGger:{mode}:LEVel", "query-set", "trigger", "volts", modes=("EDGE", "PULSE", "VIDEO")),
    _s("trigger.sweep", ":TRIGger:{mode}:SWEep", "query-set", "trigger", "AUTO|NORMal|SINGle", modes=("EDGE", "PULSE", "SLOPE", "PATTERN", "DURATION")),
    _s("trigger.coupling", ":TRIGger:{mode}:COUPling", "query-set", "trigger", "DC|AC|HF|LF", modes=("EDGE", "PULSE", "SLOPE")),
    _s("trigger.holdoff", ":TRIGger:HOLDoff", "query-set", "trigger", "seconds"),
    _s("trigger.status", ":TRIGger:STATus", "query", "trigger"),
    _s("trigger.half-level", ":Trig%50", "action", "trigger"),
    _s("trigger.force", ":FORCetrig", "action", "trigger"),
    _s("trigger.edge.slope", ":TRIGger:EDGE:SLOPe", "query-set", "trigger-edge", "POSitive|NEGative"),
    _s("trigger.edge.sensitivity", ":TRIGger:EDGE:SENSitivity", "query-set", "trigger-edge", "0.1..1 div"),
    _s("trigger.pulse.mode", ":TRIGger:PULSe:MODE", "query-set", "trigger-pulse", "+GREaterthan|+LESSthan|-GREaterthan|-LESSthan"),
    _s("trigger.pulse.sensitivity", ":TRIGger:PULSe:SENSitivity", "query-set", "trigger-pulse", "0.1..1 div"),
    _s("trigger.pulse.width", ":TRIGger:PULSe:WIDTh", "query-set", "trigger-pulse", "seconds"),
    _s("trigger.video.mode", ":TRIGger:VIDEO:MODE", "query-set", "trigger-video", "ODDfield|EVENfield|LINE|ALLLines"),
    _s("trigger.video.polarity", ":TRIGger:VIDEO:POLarity", "query-set", "trigger-video", "POSitive|NEGative"),
    _s("trigger.video.standard", ":TRIGger:VIDEO:STANdard", "query-set", "trigger-video", "NTSC|PALSecam"),
    _s("trigger.video.line", ":TRIGger:VIDEO:LINE", "query-set", "trigger-video", "line number"),
    _s("trigger.video.sensitivity", ":TRIGger:VIDEO:SENSitivity", "query-set", "trigger-video", "0.1..1 div"),
    _s("trigger.slope.time", ":TRIGger:SLOPe:TIME", "query-set", "trigger-slope", "seconds"),
    _s("trigger.slope.sensitivity", ":TRIGger:SLOPe:SENSitivity", "query-set", "trigger-slope", "0.1..1 div"),
    _s("trigger.slope.mode", ":TRIGger:SLOPe:MODE", "query-set", "trigger-slope", "+GREaterthan|+LESSthan|-GREaterthan|-LESSthan"),
    _s("trigger.slope.window", ":TRIGger:SLOPe:WINDow", "query-set", "trigger-slope", "PA|PB|NA|NB"),
    _s("trigger.slope.level-a", ":TRIGger:SLOPe:LEVelA", "query-set", "trigger-slope", "volts"),
    _s("trigger.slope.level-b", ":TRIGger:SLOPe:LEVelB", "query-set", "trigger-slope", "volts"),
    _s("trigger.pattern.pattern", ":TRIGger:PATTern:PATTern", "query-set", "trigger-pattern", "value,mask[,edge-source,edge]"),
    _s("trigger.duration.pattern", ":TRIGger:DURation:PATTern", "query-set", "trigger-duration", "value,mask"),
    _s("trigger.duration.time", ":TRIGger:DURation:TIME", "query-set", "trigger-duration", "seconds"),
    _s("trigger.duration.qualifier", ":TRIGger:DURation:QUALifier", "query-set", "trigger-duration", "GREaterthan|LESSthan"),
    _s("trigger.alternate.source", ":TRIGger:ALTernation:SOURce", "query-set", "trigger-alternate", "CHANnel1|CHANnel2"),
    _s("trigger.alternate.type", ":TRIGger:ALTernation:TYPE", "query-set", "trigger-alternate", "EDGE|PULSe|VIDEO|SLOPe"),
    _s("trigger.alternate.time-scale", ":TRIGger:ALTernation:TimeSCALe", "query-set", "trigger-alternate", "seconds/div"),
    _s("trigger.alternate.time-offset", ":TRIGger:ALTernation:TimeOFFSet", "query-set", "trigger-alternate", "seconds"),
    _s("trigger.alternate.level", ":TRIGger:ALTernation:{mode}:LEVel", "query-set", "trigger-alternate", "volts", modes=("EDGE", "PULSE", "VIDEO")),
    _s("trigger.alternate.edge.slope", ":TRIGger:ALTernation:EDGE:SLOPe", "query-set", "trigger-alternate", "POSitive|NEGative"),
    _s("trigger.alternate.mode", ":TRIGger:ALTernation:{mode}:MODE", "query-set", "trigger-alternate", "mode-specific", modes=("PULSE", "SLOPE", "VIDEO")),
    _s("trigger.alternate.time", ":TRIGger:ALTernation:{mode}:TIME", "query-set", "trigger-alternate", "seconds", modes=("PULSE", "SLOPE")),
    _s("trigger.alternate.video.polarity", ":TRIGger:ALTernation:VIDEO:POLarity", "query-set", "trigger-alternate", "POSitive|NEGative"),
    _s("trigger.alternate.video.standard", ":TRIGger:ALTernation:VIDEO:STANdard", "query-set", "trigger-alternate", "NTSC|PALSecam"),
    _s("trigger.alternate.video.line", ":TRIGger:ALTernation:VIDEO:LINE", "query-set", "trigger-alternate", "line number"),
    _s("trigger.alternate.slope.window", ":TRIGger:ALTernation:SLOPe:WINDow", "query-set", "trigger-alternate", "PA|PB|NA|NB"),
    _s("trigger.alternate.slope.level-a", ":TRIGger:ALTernation:SLOPe:LEVelA", "query-set", "trigger-alternate", "volts"),
    _s("trigger.alternate.slope.level-b", ":TRIGger:ALTernation:SLOPe:LEVelB", "query-set", "trigger-alternate", "volts"),
    _s("trigger.alternate.coupling", ":TRIGger:ALTernation:{mode}:COUPling", "query-set", "trigger-alternate", "DC|AC|HF|LF", modes=("EDGE", "PULSE", "SLOPE")),
    _s("trigger.alternate.holdoff", ":TRIGger:ALTernation:{mode}:HOLDoff", "query-set", "trigger-alternate", "seconds", modes=("EDGE", "PULSE", "SLOPE", "VIDEO")),
    _s("trigger.alternate.sensitivity", ":TRIGger:ALTernation:{mode}:SENSitivity", "query-set", "trigger-alternate", "0.1..1 div", modes=("EDGE", "PULSE", "SLOPE", "VIDEO")),
    _s("storage.factory-load", ":STORage:FACTory:LOAD", "action", "storage"),
    _s("math.display", ":MATH:DISPlay", "query-set", "math", "ON|OFF"),
    _s("math.operation", ":MATH:OPERate", "query-set", "math", "A+B|A-B|AB|FFT"),
    _s("math.fft-display", ":FFT:DISPlay", "query-set", "math", "ON|OFF"),
    _s("channel.bandwidth-limit", ":CHANnel{channel}:BWLimit", "query-set", "channel", "ON|OFF"),
    _s("channel.coupling", ":CHANnel{channel}:COUPling", "query-set", "channel", "DC|AC|GND"),
    _s("channel.display", ":CHANnel{channel}:DISPlay", "query-set", "channel", "ON|OFF"),
    _s("channel.invert", ":CHANnel{channel}:INVert", "query-set", "channel", "ON|OFF"),
    _s("channel.offset", ":CHANnel{channel}:OFFSet", "query-set", "channel", "volts"),
    _s("channel.probe", ":CHANnel{channel}:PROBe", "query-set", "channel", "1|5|10|50|100|500|1000"),
    _s("channel.scale", ":CHANnel{channel}:SCALe", "query-set", "channel", "volts/div"),
    _s("channel.filter", ":CHANnel{channel}:FILTer", "query-set", "channel", "ON|OFF"),
    _s("channel.memory-depth", ":CHANnel{channel}:MEMoryDepth", "query", "channel"),
    _s("channel.vernier", ":CHANnel{channel}:VERNier", "query-set", "channel", "ON|OFF"),
    _s("measure.clear", ":MEASure:CLEar", "action", "measure"),
    *(
        _s(f"measure.{name}", f":MEASure:{command}", "query", "measure", "optional CHANnel1|CHANnel2")
        for name, command in (
            ("vpp", "VPP"), ("vmax", "VMAX"), ("vmin", "VMIN"),
            ("vamplitude", "VAMPlitude"), ("vtop", "VTOP"), ("vbase", "VBASe"),
            ("vaverage", "VAVerage"), ("vrms", "VRMS"), ("overshoot", "OVERshoot"),
            ("preshoot", "PREShoot"), ("frequency", "FREQuency"), ("rise-time", "RISetime"),
            ("fall-time", "FALLtime"), ("period", "PERiod"), ("positive-width", "PWIDth"),
            ("negative-width", "NWIDth"), ("positive-duty", "PDUTycycle"),
            ("negative-duty", "NDUTycycle"), ("positive-delay", "PDELay"),
            ("negative-delay", "NDELay"),
        )
    ),
    _s("measure.total", ":MEASure:TOTal", "query-set", "measure", "ON|OFF"),
    _s("measure.source", ":MEASure:SOURce", "query-set", "measure", "CHANnel1|CHANnel2"),
    _s("waveform.data", ":WAVeform:DATA", "query", "waveform", "optional CHANnel1|CHANnel2|DIGital|MATH|FFT"),
    _s("waveform.points-mode", ":WAVeform:POINts:MODE", "query-set", "waveform", "NORMal|MAXimum|RAW"),
    _s("logic.display", ":LA:DISPlay", "query-set", "logic", "ON|OFF", models=("DS1000D",)),
    _s("logic.digital-turn", ":DIGital{digital}:TURN", "query-set", "logic", "ON|OFF", models=("DS1000D",)),
    _s("logic.digital-position", ":DIGital{digital}:POSition", "query-set", "logic", "0..15", models=("DS1000D",)),
    _s("logic.threshold", ":LA:THReshold", "query-set", "logic", "TTL|CMOS|ECL|user voltage", models=("DS1000D",)),
    _s("logic.position-reset", ":LA:POSition:RESet", "action", "logic", models=("DS1000D",)),
    _s("logic.group", ":LA:GROUp{group}", "query-set", "logic", "ON|OFF", models=("DS1000D",)),
    _s("logic.group-size", ":LA:GROUp{group}:SIZe", "query-set", "logic", "SMALl|BIG", models=("DS1000D",)),
    _s("key.lock", ":KEY:LOCK", "query-set", "key", "ENABle|DISable"),
    *(
        _s(f"key.{name}", f":KEY:{command}", "action", "key")
        for name, command in (
            ("run", "RUN"), ("auto", "AUTO"), ("channel1", "CHANnel1"),
            ("channel2", "CHANnel2"), ("math", "MATH"), ("reference", "REF"),
            ("f1", "F1"), ("f2", "F2"), ("f3", "F3"), ("f4", "F4"), ("f5", "F5"),
            ("menu-off", "MNUoff"), ("measure", "MEASure"), ("cursor", "CURSor"),
            ("acquire", "ACQuire"), ("display", "DISPlay"), ("storage", "STORage"),
            ("utility", "UTILity"), ("time-menu", "MNUTIME"), ("trigger-menu", "MNUTRIG"),
            ("trigger-half", "Trig%50"), ("force", "FORCe"),
            ("vertical-position-increase", "V_POS_INC"), ("vertical-position-decrease", "V_POS_DEC"),
            ("vertical-scale-increase", "V_SCALE_INC"), ("vertical-scale-decrease", "V_SCALE_DEC"),
            ("horizontal-scale-increase", "H_SCALE_INC"), ("horizontal-scale-decrease", "H_SCALE_DEC"),
            ("trigger-level-increase", "TRIG_LVL_INC"), ("trigger-level-decrease", "TRIG_LVL_DEC"),
            ("horizontal-position-increase", "H_POS_INC"), ("horizontal-position-decrease", "H_POS_DEC"),
            ("vertical-coarse-fine", "PROMPT_V"), ("delayed-toggle", "PROMPT_H"),
            ("function", "FUNCtion"), ("function-increase", "+FUNCtion"), ("function-decrease", "-FUNCtion"),
            ("vertical-position-zero", "PROMPT_V_POS"), ("horizontal-position-zero", "PROMPT_H_POS"),
            ("trigger-level-zero", "PROMPT_TRIG_LVL"), ("off", "OFF"),
        )
    ),
    _s("key.logic", ":KEY:LA", "action", "key", models=("DS1000D",)),
    _s("system.language", ":INFO:LANGuage", "query-set", "other", "SIMPlifiedChinese|TRADitionalChinese|ENGLish|KORean|JAPanese|FRENch|GERMan|RUSSian|SPANish|PORTuguese"),
    _s("counter.enable", ":COUNter:ENABle", "query-set", "other", "ON|OFF"),
    _s("beep.enable", ":BEEP:ENABle", "query-set", "other", "ON|OFF"),
    _s("beep.action", ":BEEP:ACTion", "action", "other"),
)


COMMAND_BY_NAME = {spec.name: spec for spec in COMMANDS}


def get_command(name: str) -> CommandSpec:
    try:
        return COMMAND_BY_NAME[name]
    except KeyError as exc:
        raise ProtocolError(f"unknown manual command {name!r}; use 'rigol commands list'") from exc


def render_command(spec: CommandSpec, variables: dict[str, str | int | None]) -> str:
    required = [field for field in ("channel", "digital", "group", "mode") if "{" + field + "}" in spec.command]
    missing = [field for field in required if variables.get(field) is None]
    if missing:
        flags = ", ".join("--" + item for item in missing)
        raise ProtocolError(f"{spec.name} requires {flags}")
    if variables.get("channel") not in {None, 1, 2}:
        raise ProtocolError("channel must be 1 or 2")
    if variables.get("digital") is not None and not 0 <= int(variables["digital"]) <= 15:
        raise ProtocolError("digital channel must be in range 0..15")
    if variables.get("group") not in {None, 1, 2}:
        raise ProtocolError("logic group must be 1 or 2")
    mode = variables.get("mode")
    if mode is not None:
        mode = str(mode).upper()
        if spec.modes and mode not in spec.modes:
            allowed = ", ".join(spec.modes)
            raise ProtocolError(f"{spec.name} supports --mode {allowed}; got {mode}")
        variables = {**variables, "mode": mode}
    return spec.command.format(**variables)
