import subprocess

# This command is optimized for low latency on older systems
COMMAND = (
    "stdbuf -o0 raspivid -w -vf 512 -h 512 -fps 30 -ih -t 0 -o - "
    "| nc -u -l -p 3333"
)

print("Starting low-latency video transmission...")
subprocess.call(COMMAND, shell=True)