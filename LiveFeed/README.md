This part of the code is intended to run on the raspberry pi

# Run commands to receive camera data

import os
import time

# Useful Commands

```bash
# preview camera on current setup
raspistill -f -vf -t 100000 -o preview.jpg
```

for video streaming, use:

on PI
```bash
raspivid -w 640 -h 480 -vf -q 85 -t 0 -tl 100 -o - | nc -l -k 0 -p 3333
```

on PC
```bash
ffplay -fflags nobuffer -f mjpeg tcp://<pi-ip>:3333
```
