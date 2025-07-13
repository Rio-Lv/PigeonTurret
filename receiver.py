# receiver.py - Python 3.4 compatible TCP server with serial output
import socket
import sys
import serial
import time
from serial.tools import list_ports

# Configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 4444
BAUD_RATE = 115200

# Auto-detect Arduino port (compatible with both tuple and object returns)
def auto_port():
    for p in list_ports.comports():
        # Handle both tuple (old PySerial) and object (new PySerial) formats
        if isinstance(p, tuple):
            # Old format: (port, description, hwid)
            port_name, description, _ = p
        else:
            # New format: object with attributes
            port_name = p.device
            description = p.description
        
        # Check if it's an Arduino
        if description and ('Arduino' in description or 'CH340' in description):
            return port_name
    return None

print("[*] Scanning for Arduino...")
serial_port = auto_port()
if not serial_port:
    print("❌  No Arduino found! Trying common ports...")
    # Try common ports as fallback
    common_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
    for port in common_ports:
        try:
            # Try to open to see if it exists
            ser_test = serial.Serial(port, BAUD_RATE)
            ser_test.close()
            serial_port = port
            print("[*] Using fallback port: {}".format(serial_port))
            break
        except:
            pass
    if not serial_port:
        print("❌  No serial port available. Please connect Arduino")
        sys.exit(1)
else:
    print("[*] Found Arduino at: {}".format(serial_port))

try:
    ser = serial.Serial(serial_port, BAUD_RATE, timeout=1)
    time.sleep(2)  # Allow Arduino to reset
    print("[*] Serial connected @ {} baud".format(BAUD_RATE))
    
    # Flush any initial data
    ser.flushInput()
    ser.flushOutput()
except serial.SerialException as e:
    print("❌  Serial error: {}".format(e))
    ser = None

# Create TCP socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    s.bind((HOST, PORT))
    s.listen(5)
    print("[*] TCP listening on {0}:{1}".format(HOST, PORT))
    
    while True:
        try:
            conn, addr = s.accept()
            print("[+] New connection from {0}:{1}".format(addr[0], addr[1]))
            
            while True:
                data = conn.recv(1024)
                if not data:
                    print("[-] Connection closed by client")
                    break
                    
                command = data.decode('utf-8').strip()
                print("Received command: {0}".format(command))
                
                # Forward command to Arduino if serial is available
                if ser and ser.isOpen():  # Changed to isOpen()
                    # Map state commands to single-letter commands
                    if command == "{dx:1, dy:0}":
                        ser.write(b'R')
                    elif command == "{dx:-1, dy:0}":
                        ser.write(b'L')
                    elif command == "{dx:0, dy:1}":
                        ser.write(b'D')
                    elif command == "{dx:0, dy:-1}":
                        ser.write(b'U')
                    elif command == "{dx:0, dy:0}":
                        # Stop command - release all
                        ser.write(b'l')
                        ser.write(b'r')
                        ser.write(b'u')
                        ser.write(b'd')
                
        except socket.error as e:
            if e.errno == 104:  # Connection reset by peer
                print("[-] Connection reset by peer")
            else:
                print("Socket error: {0}".format(e))
                
        except KeyboardInterrupt:
            print("\nServer interrupted")
            break
            
        finally:
            try:
                conn.close()
                print("[-] Connection closed")
            except:
                pass  # Ignore errors if conn is not defined
                
except socket.error as e:
    print("Failed to start server: {0}".format(e))
    sys.exit(1)
    
except KeyboardInterrupt:
    print("\nServer stopped by user")

finally:
    s.close()
    if ser and ser.isOpen():  # Changed to isOpen()
        ser.close()
    print("[*] Server shutdown complete")