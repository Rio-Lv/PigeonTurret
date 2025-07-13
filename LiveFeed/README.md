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

```bash
# one line
raspivid -t 0 -vf -w 640 -h 480 -fps 24 -b 2000000 -o - \
  | nc -k -l 3333
```
