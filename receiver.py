# receiver.py - Python 3.4 compatible TCP server with serial output
import socket
import sys
import serial
import time
try:
    from serial.tools import list_ports
except ImportError:
    print("Warning: Could not import serial.tools.list_ports. Using fallback ports.")

# Configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 4444
BAUD_RATE = 115200

# Auto-detect Arduino port (Python 3.4 compatible)
def auto_port():
    try:
        ports = list_ports.comports()
        for p in ports:
            # Handle both old tuple format and new object format
            if isinstance(p, tuple):
                port_name = p[0]
                description = p[1]
            else:
                port_name = p.device
                description = p.description
            
            # Check if it's an Arduino
            if description and ('Arduino' in description or 'CH340' in description or 'USB Serial' in description):
                return port_name
    except Exception as e:
        print("Warning: Port detection failed - {}".format(e))
    
    return None

print("[*] Scanning for Arduino...")
serial_port = auto_port()
if not serial_port:
    print("❌  No Arduino found! Trying common ports...")
    common_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1',
                    'COM3', 'COM4', 'COM5', 'COM6']  # Added Windows ports
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
                    
                # Handle Python 3.4 string conversion
                if isinstance(data, bytes):
                    command = data.decode('utf-8').strip()
                else:
                    command = str(data).strip()
                
                print("Received command: {0}".format(command))
                
                # Forward command to Arduino if serial is available
                if ser and ser.isOpen():  # Use isOpen() for Python 3.4 compatibility
                    # Send command with newline
                    ser.write((command + '\n').encode('utf-8'))
                    print("Forwarded to Arduino: {0}".format(command))
                
        except socket.error as e:
            if e.errno == 104:  # Connection reset by peer
                print("[-] Connection reset by peer")
            else:
                print("Socket error: {0}".format(e))
                break
                
        except KeyboardInterrupt:
            print("\nServer interrupted")
            break
            
        except Exception as e:
            print("Unexpected error: {0}".format(e))
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
    if ser and ser.isOpen():
        ser.close()
    print("[*] Server shutdown complete")