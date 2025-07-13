import subprocess

COMMAND = (
    "raspivid -w 640 -h 480 -vf -q 85 -t 0 -tl 100 -o - "
    "| nc -l -k 0 -p 3333"
)

# Blocks until the shell command exits
subprocess.call(COMMAND, shell=True)

# If you prefer to raise an exception when the command returns a
# non-zero exit code, swap for:
# subprocess.check_call(COMMAND, shell=True)
