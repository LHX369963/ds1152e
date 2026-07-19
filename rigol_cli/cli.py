from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Sequence

from .catalog import COMMANDS, get_command, render_command
from .errors import ProtocolError, RigolError, TransportError
from .transport import LinuxUsbtmc, choose_device, discover_devices
from .waveform import Waveform, parse_ieee_block, write_waveform


MEASUREMENTS = (
    "vpp", "vmax", "vmin", "vamplitude", "vtop", "vbase", "vaverage", "vrms",
    "overshoot", "preshoot", "frequency", "rise-time", "fall-time", "period",
    "positive-width", "negative-width", "positive-duty", "negative-duty",
    "positive-delay", "negative-delay",
)

SNAPSHOT_COMMANDS = {
    "acquire_type": ":ACQuire:TYPE?",
    "acquire_mode": ":ACQuire:MODE?",
    "averages": ":ACQuire:AVERages?",
    "memory_depth_mode": ":ACQuire:MEMDepth?",
    "timebase_mode": ":TIMebase:MODE?",
    "timebase_scale_seconds": ":TIMebase:SCALe?",
    "timebase_offset_seconds": ":TIMebase:OFFSet?",
    "trigger_mode": ":TRIGger:MODE?",
    "trigger_status": ":TRIGger:STATus?",
    "waveform_points_mode": ":WAVeform:POINts:MODE?",
    "channel1_display": ":CHANnel1:DISPlay?",
    "channel1_coupling": ":CHANnel1:COUPling?",
    "channel1_invert": ":CHANnel1:INVert?",
    "channel1_bandwidth_limit": ":CHANnel1:BWLimit?",
    "channel1_probe": ":CHANnel1:PROBe?",
    "channel1_scale_volts": ":CHANnel1:SCALe?",
    "channel1_offset_volts": ":CHANnel1:OFFSet?",
    "channel2_display": ":CHANnel2:DISPlay?",
    "channel2_coupling": ":CHANnel2:COUPling?",
    "channel2_invert": ":CHANnel2:INVert?",
    "channel2_bandwidth_limit": ":CHANnel2:BWLimit?",
    "channel2_probe": ":CHANnel2:PROBe?",
    "channel2_scale_volts": ":CHANnel2:SCALe?",
    "channel2_offset_volts": ":CHANnel2:OFFSet?",
}

_NEGATIVE_VALUE_PREFIX = "__RIGOL_NEGATIVE_VALUE__"


def _protect_negative_values(argv: Sequence[str]) -> list[str]:
    pattern = re.compile(r"^-(?:\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|GREaterthan|LESSthan)$", re.IGNORECASE)
    return [_NEGATIVE_VALUE_PREFIX + value if pattern.fullmatch(value) else value for value in argv]


def _restore_negative_values(args: argparse.Namespace) -> None:
    for name, value in vars(args).items():
        if isinstance(value, str) and value.startswith(_NEGATIVE_VALUE_PREFIX):
            setattr(args, name, value.removeprefix(_NEGATIVE_VALUE_PREFIX))
        elif isinstance(value, list):
            setattr(args, name, [
                item.removeprefix(_NEGATIVE_VALUE_PREFIX)
                if isinstance(item, str) and item.startswith(_NEGATIVE_VALUE_PREFIX) else item
                for item in value
            ])


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rigol", description="RIGOL DS1000E/DS1000D USBTMC CLI")
    parser.add_argument("--device", help="USBTMC node, for example /dev/usbtmc2")
    parser.add_argument("--serial", help="select an attached RIGOL by serial number")
    parser.add_argument("--timeout-ms", type=int, default=5000, help="USBTMC timeout (default: 5000)")
    parser.add_argument("--command-delay-ms", type=float, default=50.0, help="DS1152E processing delay after writes (default: 50 ms)")
    parser.add_argument("--no-clear", action="store_true", help="do not clear the USBTMC session on open")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list attached RIGOL USBTMC devices")
    sub.add_parser("info", help="query instrument identity")
    sub.add_parser("config", help="query a useful configuration snapshot")

    commands = sub.add_parser("commands", help="browse the official programming-guide command catalog")
    commands_sub = commands.add_subparsers(dest="commands_command", required=True)
    commands_list = commands_sub.add_parser("list")
    commands_list.add_argument("--section")
    commands_list.add_argument("--all-models", action="store_true", help="include DS1000D-only logic commands")
    commands_show = commands_sub.add_parser("show")
    commands_show.add_argument("name")

    for operation in ("get", "set", "action"):
        item = sub.add_parser(operation, help=f"{operation} a command from the manual catalog")
        item.add_argument("name")
        item.add_argument("values", nargs="*", help="SCPI parameter values")
        item.add_argument("--channel", type=int)
        item.add_argument("--digital", type=int)
        item.add_argument("--group", type=int)
        item.add_argument(
            "--mode",
            type=str.upper,
            choices=("EDGE", "PULSE", "VIDEO", "SLOPE", "PATTERN", "DURATION"),
        )
        if operation == "action":
            item.add_argument("--yes", action="store_true", help="confirm reset/factory-load actions")

    raw = sub.add_parser("raw", help="send an arbitrary SCPI command")
    raw.add_argument("scpi", help="complete SCPI command without a newline")
    raw.add_argument("--read", action="store_true", help="read one response after writing")
    raw.add_argument("--binary", action="store_true", help="write response bytes to --output/stdout")
    raw.add_argument("--output", type=Path)
    raw.add_argument("--max-bytes", type=int, default=2 * 1024 * 1024)

    batch = sub.add_parser("batch", help="run newline-delimited SCPI; lines ending in ? are queried")
    batch.add_argument("file", type=Path, help="command file, or - for stdin")

    measure = sub.add_parser("measure", help="query one or all automatic measurements")
    measure.add_argument("metric", choices=("all",) + MEASUREMENTS, default="all", nargs="?")
    measure.add_argument("--channel", type=int, choices=(1, 2), default=1)
    measure.add_argument("--json", action="store_true")

    waveform = sub.add_parser("waveform", help="download waveform samples")
    waveform.add_argument("--source", choices=("ch1", "ch2", "math", "fft"), default="ch1")
    waveform.add_argument("--points-mode", choices=("normal", "maximum", "raw"), default="normal")
    waveform.add_argument("--format", choices=("csv", "json", "bin"), default="csv")
    waveform.add_argument("--output", type=Path, required=True)
    waveform.add_argument("--stop", action="store_true", help="stop acquisition before transfer and resume afterward")
    waveform.add_argument("--max-bytes", type=int, default=2 * 1024 * 1024)

    return parser


def _session(args: argparse.Namespace) -> LinuxUsbtmc:
    return LinuxUsbtmc(
        choose_device(args.device, args.serial),
        timeout_ms=args.timeout_ms,
        clear_on_open=not args.no_clear,
        command_delay_ms=args.command_delay_ms,
    )


def _variables(args: argparse.Namespace) -> dict[str, str | int | None]:
    return {
        "channel": getattr(args, "channel", None),
        "digital": getattr(args, "digital", None),
        "group": getattr(args, "group", None),
        "mode": getattr(args, "mode", None),
    }


def _parse_number(value: str) -> float | str:
    try:
        number = float(value)
    except ValueError:
        return value
    if abs(number) >= 9.0e37:
        return "unavailable"
    return number


def _normalize_set_value(value: str) -> str:
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", value):
        return value
    try:
        normalized = format(Decimal(value), "f")
    except InvalidOperation:
        return value
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized or "0"


def _query_snapshot(scope: LinuxUsbtmc) -> dict[str, object]:
    result: dict[str, object] = {}
    result["identity"] = scope.query_text("*IDN?")
    for name, command in SNAPSHOT_COMMANDS.items():
        value = scope.query_text(command)
        result[name] = _parse_number(value)
    for channel in (1, 2):
        try:
            result[f"channel{channel}_sample_rate_hz"] = _parse_number(
                scope.query_text(f":ACQuire:SAMPlingrate? CHANnel{channel}")
            )
            result[f"channel{channel}_memory_depth_points"] = _parse_number(
                scope.query_text(f":CHANnel{channel}:MEMoryDepth?")
            )
        except TransportError:
            result[f"channel{channel}_sample_rate_hz"] = "unavailable"
    return result


def _measurement_command(metric: str, channel: int) -> str:
    spec = get_command("measure." + metric)
    return f"{spec.command}? CHANnel{channel}"


def _run_measure(scope: LinuxUsbtmc, metric: str, channel: int) -> dict[str, float | str]:
    names = MEASUREMENTS if metric == "all" else (metric,)
    return {name: _parse_number(scope.query_text(_measurement_command(name, channel))) for name in names}


def _capture_waveform(scope: LinuxUsbtmc, args: argparse.Namespace) -> Waveform:
    source = {"ch1": "CHANnel1", "ch2": "CHANnel2", "math": "MATH", "fft": "FFT"}[args.source]
    mode = {"normal": "NORMal", "maximum": "MAXimum", "raw": "RAW"}[args.points_mode]
    original_points_mode = scope.query_text(":WAVeform:POINts:MODE?")
    original_trigger_status = scope.query_text(":TRIGger:STATus?")
    resume_after = False
    if args.stop:
        scope.write(":STOP")
        resume_after = original_trigger_status.strip().upper() not in {"STOP", "STOPPED"}
    try:
        scope.write(f":WAVeform:POINts:MODE {mode}")
        time_scale = float(scope.query_text(":TIMebase:SCALe?"))
        time_offset = float(scope.query_text(":TIMebase:OFFSet?"))
        vertical_scale: float | None = None
        vertical_offset: float | None = None
        sample_rate: float | None = None
        if args.source in {"ch1", "ch2"}:
            channel = 1 if args.source == "ch1" else 2
            vertical_scale = float(scope.query_text(f":CHANnel{channel}:SCALe?"))
            vertical_offset = float(scope.query_text(f":CHANnel{channel}:OFFSet?"))
            sample_rate = float(scope.query_text(f":ACQuire:SAMPlingrate? CHANnel{channel}"))
        raw = parse_ieee_block(scope.query(f":WAVeform:DATA? {source}", max_bytes=args.max_bytes))
        return Waveform(source, raw, time_scale, time_offset, vertical_scale, vertical_offset, sample_rate)
    finally:
        scope.write(f":WAVeform:POINts:MODE {original_points_mode}")
        if resume_after:
            scope.write(":RUN")


def _run_batch(scope: LinuxUsbtmc, lines) -> int:
    for line_number, raw_line in enumerate(lines, start=1):
        command = raw_line.strip()
        if not command or command.startswith("#"):
            continue
        if "?" in command.split(" ", 1)[0]:
            print(scope.query_text(command))
        else:
            scope.write(command)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(_protect_negative_values(raw_argv))
    _restore_negative_values(args)
    try:
        if args.command == "list":
            for item in discover_devices():
                print(
                    f"{item.path} usb={item.vendor_id}:{item.product_id} "
                    f"serial={item.serial or '-'} product={item.product or '-'}"
                )
            return 0

        if args.command == "commands":
            if args.commands_command == "list":
                for spec in COMMANDS:
                    if args.section and spec.section != args.section:
                        continue
                    if not args.all_models and "DS1000E" not in spec.models:
                        continue
                    print(f"{spec.name:48} {spec.kind:9} {spec.command}")
                return 0
            spec = get_command(args.name)
            print(json.dumps({
                "name": spec.name,
                "command": spec.command,
                "kind": spec.kind,
                "section": spec.section,
                "parameters": spec.parameters,
                "models": list(spec.models),
                "modes": list(spec.modes),
                "description": spec.description,
            }, indent=2))
            return 0

        if args.command in {"get", "set", "action"}:
            spec = get_command(args.name)
            if "DS1000E" not in spec.models:
                raise ProtocolError(f"{spec.name} is DS1000D-only and is not available on a DS1152E")
            command = render_command(spec, _variables(args))
            if args.command == "get":
                if not spec.can_query:
                    raise ProtocolError(f"{spec.name} is not queryable")
                suffix = " " + " ".join(args.values) if args.values else ""
                with _session(args) as scope:
                    print(scope.query_text(command + "?" + suffix))
                return 0
            if args.command == "set":
                if not spec.can_write or spec.kind == "action":
                    raise ProtocolError(f"{spec.name} is not settable")
                if not args.values:
                    raise ProtocolError("set requires at least one value")
                with _session(args) as scope:
                    if spec.name == "acquire.mode":
                        value = args.values[0].strip().upper()
                        aliases = {"REAL_TIME": "RTIM", "EQUAL_TIME": "ETIM"}
                        value = aliases.get(value, value)
                        scope.write(":TIMebase:FORMat YT")
                        scope.write(f":ACQuire:MODE {value}")
                        return 0
                    scope.write(command + " " + " ".join(_normalize_set_value(value) for value in args.values))
                return 0
            if spec.kind != "action":
                raise ProtocolError(f"{spec.name} is not an action")
            if spec.name in {"general.reset", "storage.factory-load"} and not args.yes:
                raise ProtocolError(f"{spec.name} changes many settings; repeat with --yes")
            with _session(args) as scope:
                scope.write(command)
            return 0

        with _session(args) as scope:
            if args.command == "info":
                identity = scope.query_text("*IDN?")
                fields = identity.split(",")
                print(json.dumps({
                    "manufacturer": fields[0] if len(fields) > 0 else "",
                    "model": fields[1] if len(fields) > 1 else "",
                    "serial": fields[2] if len(fields) > 2 else "",
                    "software_version": fields[3] if len(fields) > 3 else "",
                    "device": str(scope.device.path),
                }, indent=2))
                return 0
            if args.command == "config":
                print(json.dumps(_query_snapshot(scope), indent=2))
                return 0
            if args.command == "raw":
                should_read = args.read or "?" in args.scpi.split(" ", 1)[0]
                if should_read:
                    data = scope.query(args.scpi, max_bytes=args.max_bytes)
                    if args.output is not None:
                        args.output.parent.mkdir(parents=True, exist_ok=True)
                        args.output.write_bytes(data)
                    elif args.binary:
                        sys.stdout.buffer.write(data)
                    else:
                        print(data.decode("ascii").strip())
                else:
                    scope.write(args.scpi)
                return 0
            if args.command == "batch":
                if str(args.file) == "-":
                    return _run_batch(scope, sys.stdin)
                try:
                    with args.file.open() as stream:
                        return _run_batch(scope, stream)
                except OSError as exc:
                    raise RigolError(f"cannot read batch file {args.file}: {exc}") from exc
            if args.command == "measure":
                values = _run_measure(scope, args.metric, args.channel)
                if args.json or args.metric == "all":
                    print(json.dumps({"channel": args.channel, "measurements": values}, indent=2))
                else:
                    print(values[args.metric])
                return 0
            if args.command == "waveform":
                waveform = _capture_waveform(scope, args)
                write_waveform(waveform, args.output, args.format)
                print(json.dumps({
                    "source": waveform.source,
                    "points": waveform.point_count,
                    "format": args.format,
                    "output": str(args.output),
                    "sample_rate_hz": waveform.sample_rate,
                }))
                return 0
        parser.error(f"unsupported command combination: {args.command}")
        return 2
    except (RigolError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
