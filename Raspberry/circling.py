#!/usr/bin/env python3
"""Send repeated jog commands to move the turret in a loop without waiting
for per-move acknowledgements. The Arduino sketch only prints "Stepper ready"
when it boots. After that we fire commands asynchronously so motion stays
smooth.
"""

import argparse
import time
import serial
from serial.tools import list_ports


def auto_port() -> str | None:
    """Return a single matching serial port, or None."""
    KEYWORDS = (
        "Arduino", "CH340", "USB2.0-Serial", "wchusbserial",
        "usbmodem", "usbserial", "FT232", "FTDI",
    )
    matches = [
        p.device
        for p in list_ports.comports()
        if any(k.lower() in f"{p.description} {p.manufacturer} {p.hwid}".lower()
               for k in KEYWORDS)
    ]
    return matches[0] if len(matches) == 1 else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Circle demo – no per move ACKs")
    default_port = auto_port()
    port_help = "Serial port (e.g. COM3 or /dev/ttyACM0)."
    if default_port:
        port_help += f" Auto-detected: {default_port}"

    parser.add_argument("-p", "--port", default=default_port, help=port_help)
    parser.add_argument("-b", "--baud", type=int, default=115200,
                        help="Baud rate (default 115200)")
    parser.add_argument("-t", "--delay", type=float, default=0.05,
                        help="Delay between commands (seconds)")
    args = parser.parse_args()

    if not args.port:
        raise SystemExit("❌  No serial port found — use --port.")

    try:
        print(f"Connecting to {args.port} @ {args.baud} baud …")
        ser = serial.Serial(args.port, args.baud, timeout=1)
        time.sleep(2)  # allow board reset
    except serial.SerialException as e:
        raise SystemExit(f"❌  Couldn't open {args.port}: {e}")

    ready = ser.readline().decode().strip()
    if ready != "Stepper ready":
        print(f"⚠️  Didn't get 'Stepper ready'. Got: {ready!r} – continuing…")

    print("✅  Sending circle jog commands. Press Ctrl+C to stop.")
    cmds = [b'u', b'r', b'd', b'l']
    try:
        while True:
            for c in cmds:
                ser.write(c)
                time.sleep(args.delay)
    except KeyboardInterrupt:
        pass
    finally:
        print("Closing serial port.")
        ser.close()


if __name__ == "__main__":
    main()
