#include <AccelStepper.h>
#define X_STEP_PIN 2
#define X_DIR_PIN  5
#define Y_STEP_PIN 3
#define Y_DIR_PIN  6
#define ENABLE_PIN 8           // single enable
#define MAX_SPEED  1000.0

AccelStepper sx(AccelStepper::DRIVER, X_STEP_PIN, X_DIR_PIN);
AccelStepper sy(AccelStepper::DRIVER, Y_STEP_PIN, Y_DIR_PIN);

void setup() {
  Serial.begin(115200);
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW);

  sx.setMaxSpeed(MAX_SPEED);
  sy.setMaxSpeed(MAX_SPEED);
  sx.setAcceleration(2000);    // optional, smoother with run()
  sy.setAcceleration(2000);
}

static char buf[32];
static byte idx = 0;

void loop() {
  while (Serial.available()) {                // non‑blocking read
    char c = Serial.read();
    if (c == '\n') {
      float dx, dy, sp;
      if (sscanf(buf, "%f,%f,%f", &dx, &dy, &sp) == 3) {
        sx.setSpeed(dx * sp * MAX_SPEED);
        sy.setSpeed(dy * sp * MAX_SPEED);
      }
      idx = 0;
    } else if (idx < sizeof(buf) - 1) {
      buf[idx++] = c;
      buf[idx]   = '\0';
    }
  }

  sx.runSpeed();    // or use run() if you enabled acceleration
  sy.runSpeed();
}