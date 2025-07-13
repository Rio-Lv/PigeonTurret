import socket

HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 4444

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Prevent address reuse
    s.bind((HOST, PORT))
    s.listen()
    print(f"[*] Listening on {HOST}:{PORT}")
    
    conn, addr = s.accept()
    print(f"[+] Connected by {addr}")
    
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(f"Received command: {data.decode()}")
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        conn.close()