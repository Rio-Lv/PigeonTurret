import subprocess

print("[*] Starting video transmission...")
COMMAND = (
    "raspivid -w 512 -h 512 -vf -fps 24 -t 0 "
    "-awb off -awbg 1.5,1.2 -sa 30 -co 20 "  
    "-o - | nc -l -k -p 3333"
)

# Blocks until the shell command exits
subprocess.call(COMMAND, shell=True)

# If you prefer to raise an exception when the command returns a
# non-zero exit code, swap for:
# subprocess.check_call(COMMAND, shell=True)