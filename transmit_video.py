import subprocess

print("[*] Starting video transmission...")
COMMAND = (
    # ─── raspivid ───────────────────────────────────────────────────────────────
    "raspivid "
    "-w 512 -h 512 "        # 1 : 1 square frame
    "-vf "                  # vertical‑flip
    "-fps 6 "               # 6 fps
    "-pf baseline "         # disable B‑frames → no encoder re‑ordering delay
    "-g 4 "                 # IDR every 4 frames (fast resync)
    "-ih "                  # put SPS/PPS in every frame (instant decoder start‑up)
    "-fl "                  # flush MMAL pipeline after each frame
    "-b 1000000 "           # ~1 Mbit/s is plenty for 512×512 @ 6 fps
    "-t 0 "                 # run forever
    # ─── built‑in UDP server ───────────────────────────────────────────────────
    "-o udp://0.0.0.0:3333" # stream over UDP (lower jitter than TCP)
)



# Blocks until the shell command exits
subprocess.call(COMMAND, shell=True)

# If you prefer to raise an exception when the command returns a
# non-zero exit code, swap for:
# subprocess.check_call(COMMAND, shell=True)