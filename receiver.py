# receiver.py - Python 3.4 compatible TCP server
import socket
import sys

HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 4444

# Create socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    s.bind((HOST, PORT))
    s.listen(5)
    print("[*] Listening on {0}:{1}".format(HOST, PORT))
    
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
                
        except socket.error as e:
            # Handle connection reset errors specifically
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
    print("[*] Server shutdown complete")