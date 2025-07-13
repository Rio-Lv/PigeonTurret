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

# Auto-detect Arduino port
def auto_port():
    for p in list_ports.comports():
        if 'Arduino' in p.description or 'CH340' in p.description:
            return p.device
    return None

# Set up serial connection
serial_port = auto_port()
if not serial_port:
    print("❌  No Arduino found! Please connect Arduino")
    serial_port = "/dev/ttyACM0"  # Default fallback

print("[*] Using serial port: {}".format(serial_port))

try:
    ser = serial.Serial(serial_port, BAUD_RATE, timeout=1)
    time.sleep(2)  # Allow Arduino to reset
    print("[*] Serial connected @ {} baud".format(BAUD_RATE))
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
                    
                command = data.decode('utf-8')
                print("Received command: {0}".format(command))
                
                # Forward command to Arduino if serial is available
                if ser and ser.is_open:
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
    if ser and ser.is_open:
        ser.close()
    print("[*] Server shutdown complete")