#include <Arduino.h>

// --- X-Axis Pins ---
const int stepX = 2;     // STEP pin for X-axis
const int dirX  = 5;     // DIR  pin for X-axis
const int enXPin = 8;    // ENABLE pin for X-axis

// --- Y-Axis Pins ---
const int stepY = 3;     // STEP pin for Y-axis
const int dirY  = 6;     // DIR  pin for Y-axis
const int enYPin = 9;    // ENABLE pin for Y-axis

// --- Motor Configuration ---
// Tweak these for your hardware and desired movement
const unsigned int stepDelayX = 3000;            // µs between step pulses
const unsigned int stepDelayY = 1500;            // µs between step pulses
const int stepsPerRevolution = 200 * 4;  // Set to match your driver’s microstepping (e.g., 200 steps/rev * 4x microstepping)
const int turnAmountX = stepsPerRevolution / 64; // Move 1/64 of a full rotation (5.625°) per key press
const int turnAmountY = stepsPerRevolution / 64; // Move 1/64 of a full rotation (5.625°) per key press

/**
 * @brief Pulses the X-axis STEP pin once to move one step.
 */
void singleStepX() {
  digitalWrite(stepX, HIGH);
  delayMicroseconds(stepDelayX);
  digitalWrite(stepX, LOW);
  delayMicroseconds(stepDelayX);
}

/**
 * @brief Pulses the Y-axis STEP pin once to move one step.
 */
void singleStepY() {
  digitalWrite(stepY, HIGH);
  delayMicroseconds(stepDelayY);
  digitalWrite(stepY, LOW);
  delayMicroseconds(stepDelayY);
}

/**
 * @brief Rotates the X-axis motor a given number of steps.
 * @param steps Number of steps to rotate.
 * @param clockwise Direction of rotation (true for clockwise).
 */
void rotateStepsX(int steps, bool clockwise) {
  digitalWrite(dirX, clockwise ? HIGH : LOW);
  for (int i = 0; i < steps; ++i) {
    singleStepX();
  }
}

/**
 * @brief Rotates the Y-axis motor a given number of steps.
 * @param steps Number of steps to rotate.
 * @param clockwise Direction of rotation (true for clockwise).
 */
void rotateStepsY(int steps, bool clockwise) {
  digitalWrite(dirY, clockwise ? HIGH : LOW);
  for (int i = 0; i < steps; ++i) {
    singleStepY();
  }
}

void setup() {
  // --- Initialize Pins ---
  // X-Axis
  pinMode(stepX, OUTPUT);
  pinMode(dirX,  OUTPUT);
  pinMode(enXPin, OUTPUT);
  digitalWrite(enXPin, LOW);     // Enable X-axis driver (LOW = enabled for A4988/DRV8825)

  // Y-Axis
  pinMode(stepY, OUTPUT);
  pinMode(dirY,  OUTPUT);
  pinMode(enYPin, OUTPUT);
  digitalWrite(enYPin, LOW);     // Enable Y-axis driver

  // --- Initialize Serial Communication ---
  Serial.begin(115200);
  Serial.println(F("Stepper ready")); // Use F() macro to save RAM
}


void loop() {
  // Check if there is data available to read from the serial port
  if (Serial.available()) {
    // Read the incoming character
    char cmd = Serial.read();

    // Act based on the command received
    switch (cmd) {
      case 'l': rotateStepsX(turnAmountX, true);  break;  // Left arrow: X-axis forward
      case 'r': rotateStepsX(turnAmountX, false); break;  // Right arrow: X-axis backward
      case 'u': rotateStepsY(turnAmountY, false); break;  // Up arrow: Y-axis left
      case 'd': rotateStepsY(turnAmountY, true);  break;  // Down arrow: Y-axis right

      // You can add more cases for different movements
      // case 'U': rotateStepsX(stepsPerRevolution, true);  break;
      
      default:
        // Ignore any other characters
        break;
    }
  }
}
