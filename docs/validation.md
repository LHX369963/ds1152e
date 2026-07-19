# DS1152E Validation

Validation date: 2026-07-19

## Instrument

```text
Rigol Technologies,DS1152E,DS1ET192605874,00.04.01.00.02
/dev/usbtmc2
```

The generator connection used for analog checks was DG1022 CH1 to DS1152E CH1
and DG1022 CH2 to DS1152E CH2.

## Catalog Audit

- 164 merged manual catalog entries
- 156 entries applicable to DS1000E/DS1152E
- 8 DS1000D-only logic entries correctly rejected on DS1152E
- 104 query-capable DS1000E entries
- 160 allowed query instances after expanding channels, trigger modes, and
  measurement sources
- 160/160 allowed instances returned a response on the instrument

An initial unconstrained expansion found 14 invalid trigger-mode combinations.
The programming guide confirms those paths do not exist. `CommandSpec.modes` now
models each command's allowed modes, and the CLI rejects unsupported combinations
before opening the instrument.

Query-set original-value writeback covered 112 expanded instances. 106 round
tripped the instrument response verbatim. Six require the guide's input spelling
instead of the display response: sensitivity values need ordinary decimal notation,
and pattern query output must be reduced to its settable value/mask fields. Those
paths were written with valid normalized values and restored.

Action dispatch, confirmation gating for reset/factory load, arbitrary raw SCPI,
and batch dispatch are covered by unit tests or live command use. `HARDcopy` needs
a USB storage device in the scope's host port to prove creation of the bitmap; no
such storage device was part of this setup, so only command availability is claimed.

## Waveform Calibration

The analog conversion was checked with five DC levels from the DG1022. The correct
DS1000E conversion reference is byte 125:

```text
volts = (125 - raw) * scale / 25 - offset
```

At a -1 V generator level, the scope automatic average was -1.02 V and exported
CSV mean was -1.023 V. With 0 V input and +0.5 V scope vertical offset, exported
samples reconstructed approximately -5 mV.

Waveform download restores the original points mode. The final points mode after
validation was `MAXIMUM`.

## Final Connected Baseline

```text
DG CH1 -> DS CH1: 1.000 kHz, 2.04 Vpp
DG CH2 -> DS CH2: 1.980 kHz, 2.02 Vpp
DS channels: display ON, DC, probe 1X, 0.5 V/div, offset 0 V
DS invert: OFF/OFF
DS bandwidth limit: OFF/OFF
DS timebase: 200 us/div
```

Unit test result: 15 passed.
