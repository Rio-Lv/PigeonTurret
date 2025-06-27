#include <Stepper.h>

const int stepsPerRevolution = 200; // Adjust this based on your motor's specifications [1, 3]
const int motorPin1 = 8;
const int motorPin2 = 9;
const int motorPin3 = 10;
const int motorPin4 = 11;

Stepper myStepper(stepsPerRevolution, motorPin1, motorPin2, motorPin3, motorPin4);

void setup() {
  myStepper.setSpeed(60); // Set speed to 60 RPM [4, 5]
  Serial.begin(9600); // For debugging
}

void loop() {
  Serial.println("Clockwise");
  myStepper.step(stepsPerRevolution); // Rotate one revolution clockwise [4, 5]
  delay(500);

  Serial.println("Counterclockwise");
  myStepper.step(-stepsPerRevolution); // Rotate one revolution counterclockwise [4, 5]
  delay(500);
}