"""
control.py - Send arrow key commands over TCP to Raspberry Pi
Hold arrow keys for continuous motion, release to stop. Esc quits.
"""
import argparse
import sys
import time
import socket
from pynput import keyboard

# TCP configuration
PI_IP = "192.168.1.120"  # Replace with your Pi's IP
PORT = 4444

# Initialize socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect_to_pi():
    """Establish connection to Raspberry Pi"""
    try:
        sock.connect((PI_IP, PORT))
        print(f"✅  Connected to {PI_IP}:{PORT}")
        return True
    except ConnectionRefusedError:
        print(f"❌  Connection refused. Is receiver.py running on {PI_IP}:{PORT}?")
        return False
    except OSError as e:
        print(f"❌  Connection error: {e}")
        return False

print("⌨️  Ready. Hold ← → ↑ ↓. Esc to quit.")

# Key-handling maps
PRESS_MAP = {
    keyboard.Key.left: 'L',
    keyboard.Key.right: 'R',
    keyboard.Key.up: 'U',
    keyboard.Key.down: 'D'
}

RELEASE_MAP = {
    keyboard.Key.left: 'l',
    keyboard.Key.right: 'r',
    keyboard.Key.up: 'u',
    keyboard.Key.down: 'd'
}

# Movement state tracking
movement_state = {
    'dx': 0,
    'dy': 0
}

def send_command(cmd_type, key):
    """Send command to Raspberry Pi and update movement state"""
    # Map key to direction vector
    if key == keyboard.Key.left:
        movement_state['dx'] = -1 if cmd_type == 'press' else 0
    elif key == keyboard.Key.right:
        movement_state['dx'] = 1 if cmd_type == 'press' else 0
    elif key == keyboard.Key.up:
        movement_state['dy'] = -1 if cmd_type == 'press' else 0
    elif key == keyboard.Key.down:
        movement_state['dy'] = 1 if cmd_type == 'press' else 0
    
    # Format command string
    command_str = f"{{dx:{movement_state['dx']}, dy:{movement_state['dy']}}}"
    
    # Send via TCP
    try:
        sock.sendall(command_str.encode())
        print(f"📤 Sent: {command_str}")
    except (BrokenPipeError, ConnectionResetError, OSError):
        print("❌  Connection lost! Attempting to reconnect...")
        if connect_to_pi():
            sock.sendall(command_str.encode())
            print(f"📤 Re-sent: {command_str}")

def on_press(key):
    """Handle key press events"""
    if key in PRESS_MAP:
        send_command('press', key)
        return PRESS_MAP[key]

def on_release(key):
    """Handle key release events"""
    if key in RELEASE_MAP:
        send_command('release', key)
        return RELEASE_MAP[key]
    if key == keyboard.Key.esc:
        print("👋 Bye!")
        return False  # stop listener

# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control robot via TCP')
    parser.add_argument('--ip', default=PI_IP, help=f'Raspberry Pi IP (default: {PI_IP})')
    args = parser.parse_args()
    PI_IP = args.ip
    
    if not connect_to_pi():
        sys.exit(1)
    
    # Create listener
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    
    try:
        while True:
            time.sleep(0.1)  # Keep main thread alive
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        sock.close()
        print("🔌 Connection closed. Clean exit.")