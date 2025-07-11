#include <Arduino.h>

const int stepX = 2;     // STEP pin
const int dirX  = 5;     // DIR  pin
const int enPin = 8;     // ENABLE pin

// Tweak these for your hardware
const int stepDelay = 1000;              // µs between rising edges
const int stepsPerRevolution = 200 * 4;  // matches your driver’s µstep mode
const int quarterTurn = stepsPerRevolution / 4; // 90° worth of steps

void singleStep() {
  digitalWrite(stepX, HIGH);
  delayMicroseconds(stepDelay);
  digitalWrite(stepX, LOW);
  delayMicroseconds(stepDelay);
}

void rotateSteps(int steps, bool clockwise) {
  digitalWrite(dirX, clockwise ? HIGH : LOW);
  for (int i = 0; i < steps; ++i) singleStep();
}

void setup() {
  pinMode(stepX, OUTPUT);
  pinMode(dirX,  OUTPUT);
  pinMode(enPin, OUTPUT);
  digitalWrite(enPin, LOW);     // enable driver

  Serial.begin(115200);
  Serial.println(F("Stepper ready"));
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();

    switch (cmd) {
      case 'u': rotateSteps(quarterTurn, true);  break;  // ↑  pressed
      case 'd': rotateSteps(quarterTurn, false); break;  // ↓  pressed
      // Add more cases if you want finer or coarser moves:
      // case 'U': rotateSteps(stepsPerRevolution, true);  break;   // full rev CW
      // case 'D': rotateSteps(stepsPerRevolution, false); break;   // full rev CCW
      default:   /* ignore anything else */            break;
    }
  }
}
