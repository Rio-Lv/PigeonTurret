const int motorStepPin = 2;
const int motorDirPin = 5;

const int stepDelayMicroseconds = 500; // Adjust for speed: smaller = faster
const long stepsToSpin = 5000; // Adjust for duration: more steps = longer spin

void setup() {
  pinMode(motorStepPin, OUTPUT);
  pinMode(motorDirPin, OUTPUT);

  // Spin clockwise for a set number of steps
  digitalWrite(motorDirPin, HIGH); // Set direction
  for (long i = 0; i < stepsToSpin; i++) {
    digitalWrite(motorStepPin, HIGH);
    delayMicroseconds(stepDelayMicroseconds);
    digitalWrite(motorStepPin, LOW);
    delayMicroseconds(stepDelayMicroseconds);
  }
  // Motor stops after this loop completes
}

void loop() {
  // Empty loop, motor stops after setup completes its spin
}
