import subprocess

print("[*] Starting video transmission...")
COMMAND = (
    "raspivid -w 256 -h 256 -vf -fps 3  -t 0 -o - | nc -l -k -p 3333"
)  # Start the camera streaming command

# Blocks until the shell command exits
subprocess.call(COMMAND, shell=True)

# If you prefer to raise an exception when the command returns a
# non-zero exit code, swap for:
# subprocess.check_call(COMMAND, shell=True)
