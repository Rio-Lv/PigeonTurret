import subprocess

print("[*] Starting video transmission...")
COMMAND = (
    "raspivid -w 1028 -h 1028 -vf -fps 12 -t 0 "
    "-o - | nc -l -k -p 3333"
)

# Blocks until the shell command exits
subprocess.call(COMMAND, shell=True)

# If you prefer to raise an exception when the command returns a
# non-zero exit code, swap for:
# subprocess.check_call(COMMAND, shell=True)