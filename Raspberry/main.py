#!/usr.bin/env python3
"""
control.py – Drive the Arduino stepper sketch with ↑ / ↓ arrow keys.
"""
import argparse
import sys
import time
import serial
from serial.tools import list_ports
from pynput import keyboard

def auto_port():
    """Attempts to find a connected Arduino port."""
    # Look for devices with common Arduino-related strings in their description
    matches = [p.device for p in list_ports.comports() if 'Arduino' in p.description or 'CH340' in p.description]
    return matches[0] if len(matches) == 1 else None

def main():
    """Main function to run the keyboard controller."""
    parser = argparse.ArgumentParser(description="Control Arduino stepper with arrow keys.")
    
    default_port = auto_port()
    port_help = "Serial port (e.g., COM3 or /dev/ttyACM0)."
    if default_port:
        port_help += f" Auto-detected: {default_port}"

    parser.add_argument("-p", "--port", default=default_port, help=port_help)
    parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate (default 115200)")
    args = parser.parse_args()

    if not args.port:
        sys.exit("❌ Error: No serial port found. Please specify one with the --port flag.")

    try:
        print(f"Connecting to {args.port} at {args.baud} baud...")
        ser = serial.Serial(args.port, args.baud, timeout=1)
        # Allow time for the Arduino to reset after establishing a serial connection
        time.sleep(2)
    except serial.SerialException as e:
        sys.exit(f"❌ Error: Could not open serial port '{args.port}': {e}")

    # Wait for the "Stepper ready" message from the Arduino
    ready_message = ser.readline().decode('utf-8').strip()
    if ready_message != "Stepper ready":
        print(f"⚠️  Warning: Did not receive 'Stepper ready' message. Got: '{ready_message}'")
        print("Continuing anyway...")
        
    print("\n✅ Connection successful. Press ↑ or ↓ to move the motor. Press Esc to quit.")

    def on_press(key):
        try:
            if key == keyboard.Key.up:
                print("↑  Up command sent")
                ser.write(b'u')
            elif key == keyboard.Key.down:
                print("↓  Down command sent")
                ser.write(b'd')
            elif key == keyboard.Key.left:
                print("←  Left command sent")
                ser.write(b'l')
            elif key == keyboard.Key.right:
                print("→  Right command sent")
                ser.write(b'r')
            elif key == keyboard.Key.esc:
                print("Exiting...")
                return False  # Stop listener    
        except serial.SerialException:
            print("⚠️  Error: Lost connection to serial port.")
            return False

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    listener.join() # Wait for the listener to stop

    print("Closing serial port.")
    ser.close()

if __name__ == "__main__":
    main()