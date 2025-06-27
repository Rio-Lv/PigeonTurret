// Define the STEP and DIR pins for your motor on the CNC Shield
// These are typical pin assignments for the X-axis on a CNC Shield v3
const int motorStepPin = 2; // X-STEP pin on CNC Shield
const int motorDirPin = 5;  // X-DIR pin on CNC Shield

// Define the delay between steps (controls speed)
// Smaller delay = faster motor (but too small means missed steps)
// Start with a large delay for slow, reliable movement.
const int stepDelayMicroseconds = 1000; // 1000 microseconds = 1 millisecond

// Define the number of steps for a full revolution for your motor
// If you are using microstepping (e.g., 1/16th), multiply this value by 16.
// For a 200 step/rev motor at 1/16 microstepping, one "revolution" is 200 * 16 = 3200 steps.
const long stepsPerRevolution_microsteps = 200 * 16; // Example for 1.8 deg motor with 1/16 microstepping

void setup() {
  // Set the pin modes for the step and direction pins
  pinMode(motorStepPin, OUTPUT);
  pinMode(motorDirPin, OUTPUT);

  Serial.begin(9600);
  Serial.println("Arduino Direct Stepper Control Ready!");
}

void loop() {
  // === Move Clockwise ===
  Serial.println("Moving Clockwise one revolution...");
  digitalWrite(motorDirPin, HIGH); // Set direction for clockwise (adjust HIGH/LOW if it's the wrong way)

  for (long i = 0; i < stepsPerRevolution_microsteps; i++) {
    digitalWrite(motorStepPin, HIGH); // Pulse the step pin HIGH
    delayMicroseconds(stepDelayMicroseconds); // Hold HIGH for a short duration
    digitalWrite(motorStepPin, LOW);  // Pull the step pin LOW
    delayMicroseconds(stepDelayMicroseconds); // Hold LOW for a short duration (pulse width + interval)
  }
  delay(1000); // Pause for 1 second at the end of the move

  // === Move Counter-clockwise ===
  Serial.println("Moving Counterclockwise one revolution...");
  digitalWrite(motorDirPin, LOW); // Set direction for counter-clockwise (adjust HIGH/LOW as needed)

  for (long i = 0; i < stepsPerRevolution_microsteps; i++) {
    digitalWrite(motorStepPin, HIGH);
    delayMicroseconds(stepDelayMicroseconds);
    digitalWrite(motorStepPin, LOW);
    delayMicroseconds(stepDelayMicroseconds);
  }
  delay(1000); // Pause for 1 second at the end of the move
}