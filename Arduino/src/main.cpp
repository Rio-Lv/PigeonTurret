#include <Arduino.h>
const int stepX = 2;  // Step signal pin
const int dirX  = 5;  // Direction signal pin
const int enPin = 8;  // Enable signal pin

// Fixed speed delay in microseconds (adjust this for your desired speed)
const int stepDelay = 1000; // 1 ms delay between step edges

// Steps per full revolution of the motor. Adjust to match your driver
// microstepping configuration. With a typical 1.8° stepper at full step
// this would be 200.
const int stepsPerRevolution = 200;

// Number of steps required for a 90° (quarter turn) move.
const int quarterTurnSteps = stepsPerRevolution / 4;

// Perform a single step taking the configured delay into account
void singleStep() {
  digitalWrite(stepX, HIGH);
  delayMicroseconds(stepDelay);
  digitalWrite(stepX, LOW);
  delayMicroseconds(stepDelay);
}

// Rotate the motor a given number of steps in the specified direction
void rotateSteps(int steps, bool clockwise) {
  digitalWrite(dirX, clockwise ? HIGH : LOW);
  for (int i = 0; i < steps; ++i) {
    singleStep();
  }
}

void setup() {
  pinMode(stepX, OUTPUT);
  pinMode(dirX, OUTPUT);
  pinMode(enPin, OUTPUT);

  digitalWrite(enPin, LOW); // Enable the motor driver
}

void loop() {
  // Rotate 90° clockwise
  rotateSteps(quarterTurnSteps, true);
  delay(500); // Small pause

  // Rotate 90° back to the starting position
  rotateSteps(quarterTurnSteps, false);
  delay(500);
}
