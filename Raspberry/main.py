"""
control.py Hold the arrow keys for continuous motion,
release to stop. Esc quits.
"""
import argparse, sys, time, serial
from serial.tools import list_ports
from pynput import keyboard


# # -- initiate camera streaming --
# try:
#     subprocess.Popen("raspivid -w 640 -h 480 -vf -q 85 -t 0 -tl 100 -o - | nc -l -k 0 -p 3333", shell=True)
# except Exception as e:
#     sys.exit("Failed to start camera streaming: {}".format(e))

# ── Helper: auto-detect Arduino port ───────────────────────
def auto_port():
    for p in list_ports.comports():
        if 'Arduino' in p.description or 'CH340' in p.description:
            return p.device
    return None

# ── CLI args ───────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Continuous arrow-key control")
def_port = auto_port()
help_port = "Serial port (auto: {})".format(def_port) if def_port else "Serial port (e.g. /dev/ttyUSB0)"
parser.add_argument("-p", "--port", default=def_port, help=help_port)
parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate (default 115200)")
args = parser.parse_args()
if not args.port:
    sys.exit("❌  No serial port found; use --port")

# ── Open serial ────────────────────────────────────────────
try:
    print("Connecting to {} @ {} baud …".format(args.port, args.baud))
    ser = serial.Serial(args.port, args.baud, timeout=1)
    time.sleep(2)  # allow Arduino reset
except serial.SerialException as e:
    sys.exit("❌  {}".format(e))

# Wait for banner (optional)
ser.readline()

print("✅  Ready. Hold ← → ↑ ↓. Esc to quit.")

# ── Key-handling maps ──────────────────────────────────────
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

def on_press(key):
    if key in PRESS_MAP:
        ser.write(PRESS_MAP[key].encode())

def on_release(key):
    if key in RELEASE_MAP:
        ser.write(RELEASE_MAP[key].encode())
    if key == keyboard.Key.esc:
        print("Bye!")
        return False  # stop listener

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
    ser.close()
    print("Clean exit")