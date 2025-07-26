import serial
import time
import json


STEPS_PER_SCREEN_WIDTH = 1500  # More or less Steps per Screen Width/Height
L = STEPS_PER_SCREEN_WIDTH # Length of the motion range in steps
# List of coordinates to move to in sequence
COORDS = [
    {"x": 0, "y": 0},
    {"x": 0, "y": L},
]

SERIAL_PORT = '/dev/tty.usbmodem14201'
BAUD_RATE = 115200


def find_arduino_port():
    """Try to locate a serial port that looks like an Arduino."""
    from serial.tools import list_ports

    KEYWORDS = ("arduino", "usbmodem", "ch340")
    for port in list_ports.comports():
        for keyword in KEYWORDS:
            if keyword in port.description.lower() or keyword in port.device.lower():
                print(f"Found potential Arduino on {port.device}")
                return port.device
    return None


def go(coords):
    """Send a sequence of absolute coordinates to the Arduino."""
    port = find_arduino_port()
    if not port:
        print("Error: Could not automatically find Arduino port.")
        port = SERIAL_PORT

    print(f"Connecting to Arduino on {port} at {BAUD_RATE} bps...")

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=10)
        time.sleep(2)
        print(f"Arduino says: {ser.readline().decode().strip()}")
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {port}. Details: {e}")
        return

    print("Starting motion control. Press Ctrl+C to stop.")

    try:
        for coord in coords:
            command_str = json.dumps(coord) + '\n'
            print(f"Sending: {command_str.strip()}...")
            ser.write(command_str.encode('utf-8'))
            response = ser.readline().decode().strip()
            print(f"Arduino acknowledged: '{response}'")

        # Return to origin after completion
        command_obj = {"x": 0, "y": 0}
        command_str = json.dumps(command_obj) + '\n'
        ser.write(command_str.encode('utf-8'))
        response = ser.readline().decode().strip()
        print(f"Arduino acknowledged final move: '{response}'")
    except KeyboardInterrupt:
        print("\nStopping motion. Returning to origin (0,0)...")
        command_obj = {"x": 0, "y": 0}
        command_str = json.dumps(command_obj) + '\n'
        ser.write(command_str.encode('utf-8'))
        response = ser.readline().decode().strip()
        print(f"Arduino acknowledged final move: '{response}'")
    finally:
        if ser.is_open:
            ser.close()
            print("Serial port closed.")


if __name__ == "__main__":
    go(COORDS)

