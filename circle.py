import serial
import time
import json
import math

# --- Configuration ---
SERIAL_PORT = '/dev/tty.usbmodem14201' 
BAUD_RATE = 115200

# --- Motion Parameters ---
RADIUS = 1000
ROTATION_PERIOD = 100.0 # Time for a full circle if moves were instant

def find_arduino_port():
    """Tries to find a serial port that looks like an Arduino."""
    from serial.tools import list_ports
    KEYWORDS = ("arduino", "usbmodem", "ch340")
    for port in list_ports.comports():
        for keyword in KEYWORDS:
            if keyword in port.description.lower() or keyword in port.device.lower():
                print(f"Found potential Arduino on {port.device}")
                return port.device
    return None

def main():
    """
    Main function to connect to Arduino and send coordinate commands,
    waiting for acknowledgment after each move.
    """
    port = find_arduino_port()
    if not port:
        print("Error: Could not automatically find Arduino port.")
        port = SERIAL_PORT

    print(f"Connecting to Arduino on {port} at {BAUD_RATE} bps...")

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=10) # Set a longer timeout
        time.sleep(2) 
        print(f"Arduino says: {ser.readline().decode().strip()}")
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {port}. Details: {e}")
        return

    print("Starting motion control. Press Ctrl+C to stop.")
    
    start_time = time.time()
    # Define how many steps make up the circle
    CIRCLE_STEPS = 100 

    try:
        for i in range(CIRCLE_STEPS):
            # Calculate the angle for the current point
            angle = (i / CIRCLE_STEPS) * 2 * math.pi
            
            # Calculate the target absolute position on the circle
            target_x = round(RADIUS * math.cos(angle))
            target_y = round(RADIUS * math.sin(angle))
            
            # Create and send the JSON command
            command_obj = {"x": target_x, "y": target_y}
            command_str = json.dumps(command_obj) + '\n'
            
            print(f"Sending: {command_str.strip()}...")
            ser.write(command_str.encode('utf-8'))
            
            # MODIFIED: Wait for the "done" acknowledgment from the Arduino
            response = ser.readline().decode().strip()
            print(f"Arduino acknowledged: '{response}'")

            # Loop forever by resetting i
            if i == CIRCLE_STEPS - 1:
                i = -1 
        # Return to origin on after circle completion 
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
        # Wait for the final acknowledgment
        response = ser.readline().decode().strip()
        print(f"Arduino acknowledged final move: '{response}'")
        
    finally:
        if ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()