import subprocess

print("[*] Starting video transmission...")
COMMAND = (
    # ─── raspivid ───────────────────────────────────────────────────────────────
    "raspivid "
    "-w 512 -h 512         "   # keep your 1:1 square frame
    "-vf -fps 6            "   # vertical‑flip, 6 fps
    "-pf baseline          "   # no B‑frames → no encoder re‑ordering delay
    "-g 4                  "   # send an IDR every 4 frames so the client can resync fast
    "-ih                   "   # put SPS/PPS in every frame for instant decoder start‑up :contentReference[oaicite:0]{index=0}
    "-fl                   "   # flush the MMAL pipeline after each frame :contentReference[oaicite:1]{index=1}
    "-b 1000000            "   # ~1 Mbit/s is plenty for 512×512@6 fps
    "-t 0                  "   # run forever
    # ─── built‑in server instead of netcat ─────────────────────────────────────
    "-l -o udp://0.0.0.0:3333" # listen & stream over UDP (lower jitter than TCP) :contentReference[oaicite:2]{index=2}
)


# Blocks until the shell command exits
subprocess.call(COMMAND, shell=True)

# If you prefer to raise an exception when the command returns a
# non-zero exit code, swap for:
# subprocess.check_call(COMMAND, shell=True)