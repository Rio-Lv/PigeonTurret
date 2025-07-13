"""
control.py - Send arrow key commands over TCP
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
        print("✅  Connected to {0}:{1}".format(PI_IP, PORT))
        return True
    except ConnectionRefusedError:
        print("❌  Connection refused. Is receiver.py running?")
        return False
    except OSError as e:
        print("❌  Connection error: {0}".format(e))
        return False

print("⌨️  Ready. Hold ← → ↑ ↓. Esc to quit.")

# Movement state tracking
movement_state = {
    'dx': 0,
    'dy': 0
}

def send_command():
    """Send current state to Raspberry Pi"""
    command_str = "{{dx:{dx}, dy:{dy}}}".format(**movement_state)
    try:
        sock.sendall(command_str.encode())
        print("📤 Sent: {0}".format(command_str))
    except (BrokenPipeError, ConnectionResetError, OSError):
        print("❌  Connection lost! Attempting to reconnect...")
        if connect_to_pi():
            sock.sendall(command_str.encode())
            print("📤 Re-sent: {0}".format(command_str))

def on_press(key):
    """Handle key press events"""
    if key == keyboard.Key.left:
        movement_state['dx'] = -1
    elif key == keyboard.Key.right:
        movement_state['dx'] = 1
    elif key == keyboard.Key.up:
        movement_state['dy'] = -1
    elif key == keyboard.Key.down:
        movement_state['dy'] = 1
    else:
        return
    
    send_command()

def on_release(key):
    """Handle key release events"""
    if key in (keyboard.Key.left, keyboard.Key.right):
        movement_state['dx'] = 0
    elif key in (keyboard.Key.up, keyboard.Key.down):
        movement_state['dy'] = 0
    elif key == keyboard.Key.esc:
        print("👋 Bye!")
        return False  # stop listener
    else:
        return
    
    send_command()

# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control robot via TCP')
    parser.add_argument('--ip', default=PI_IP, help='Raspberry Pi IP')
    args = parser.parse_args()
    PI_IP = args.ip
    
    if not connect_to_pi():
        sys.exit(1)
    
    # Create listener
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            pass
        finally:
            sock.close()
            print("🔌 Connection closed. Clean exit.")