import subprocess 

COMMAND = "raspivid -w 640 -h 480 -vf -q 85 -t 0 -tl 100 -o - | nc -l -k 0 -p 3333"
subprocess.run(COMMAND, shell=True)