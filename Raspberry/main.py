#!/usr/bin/env python3
"""
control.py – Drive the Arduino stepper sketch with ↑ ↓ ← → arrow keys.
Send:
    ↑  … b'u'
    ↓  … b'd'
    ←  … b'l'
    →  … b'r'
"""
import argparse
import sys
import time
import serial
from serial.tools import list_ports
from pynput import keyboard


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
    """Run the keyboard controller."""
    parser = argparse.ArgumentParser(
        description="Control Arduino stepper with ↑ ↓ ← → arrow keys."
    )
    default_port = auto_port()
    port_help = "Serial port (e.g. COM3 or /dev/ttyACM0)."
    if default_port:
        port_help += f" Auto‑detected: {default_port}"

    parser.add_argument("-p", "--port", default=default_port, help=port_help)
    parser.add_argument("-b", "--baud", type=int, default=115200,
                        help="Baud rate (default 115200)")
    args = parser.parse_args()

    if not args.port:
        sys.exit("❌  No serial port found — use --port.")

    try:
        print(f"Connecting to {args.port} @ {args.baud} baud …")
        ser = serial.Serial(args.port, args.baud, timeout=1)
        time.sleep(2)          # give the MCU time to reset
    except serial.SerialException as e:
        sys.exit(f"❌  Couldn’t open {args.port}: {e}")

    ready = ser.readline().decode().strip()
    if ready != "Stepper ready":
        print(f"⚠️  Didn’t get 'Stepper ready'. Got: “{ready}” – continuing…")

    print("✅  Connected. Press ↑ ↓ ← → to move, Esc to quit.")

    def on_press(key):
        try:
            if key == keyboard.Key.up:
                print("↑  Up command")
                ser.write(b'u')
            elif key == keyboard.Key.down:
                print("↓  Down command")
                ser.write(b'd')
            elif key == keyboard.Key.left:
                print("←  Left command")
                ser.write(b'l')
            elif key == keyboard.Key.right:
                print("→  Right command")
                ser.write(b'r')
            elif key == keyboard.Key.esc:
                print("Exiting…")
                return False
        except serial.SerialException:
            print("⚠️  Lost serial connection.")
            return False

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    print("Closing serial port.")
    ser.close()


if __name__ == "__main__":
    main()
