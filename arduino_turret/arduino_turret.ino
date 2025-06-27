const int stepX = 2; // Step signal pin
const int dirX  = 5; // Direction signal pin
const int enPin = 8; // Enable signal pin

// Fixed speed delay in microseconds (adjust this for your desired speed)
const int stepDelay =1000; // 500 µs delay for a reasonable speed (higher = slower)

void setup() {
  pinMode(stepX, OUTPUT);
  pinMode(dirX, OUTPUT);
  pinMode(enPin, OUTPUT);

  digitalWrite(enPin, LOW); // Enable the motor driver
  digitalWrite(dirX, HIGH); // Set direction to clockwise
}

void loop() {
  while (true) { // Continuous rotation
    digitalWrite(stepX, HIGH);
    delayMicroseconds(stepDelay); // Delay determines speed
    digitalWrite(stepX, LOW);
    delayMicroseconds(stepDelay);
  }
}
