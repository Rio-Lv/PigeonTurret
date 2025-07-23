# PigeonTurret Python Tools

This folder contains helper scripts to drive the stepper-turret from a host computer.

* `main.py` – control the turret manually with the arrow keys.
* `circling.py` – send continuous jog commands in a loop. This keeps motion smooth because it does **not** wait for a `done` acknowledgement after each move. The Arduino sketch only prints `Stepper ready` once at boot.

The default `circle.py` in the repository uses blocking acknowledgements and can lead to jitter. Use `circling.py` along with the "Serial Jog Demo" firmware for smoother motion and track position by summing the jog commands you send.
