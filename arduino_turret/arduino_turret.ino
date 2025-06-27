#include <AccelStepper.h>

// Define stepper motor connections
#define motorPin1  8
#define motorPin2  9
#define motorPin3 10
#define motorPin4 11

// Define a stepper and the pins it will use
AccelStepper stepper(AccelStepper::FULL4WIRE, motorPin1, motorPin3, motorPin2, motorPin4);

void setup() {
  // Set the maximum speed and acceleration
  stepper.setMaxSpeed(200.0);
  stepper.setAcceleration(100.0);

  // Serial output for debugging
  Serial.begin(9600);
}

void loop() {
  if (stepper.distanceToGo() == 0) {
    stepper.moveTo(stepper.currentPosition() + 200); // Move 200 steps forward
  }
  stepper.run(); // Call this in the loop
}