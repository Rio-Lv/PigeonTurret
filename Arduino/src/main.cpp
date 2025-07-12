/**
 * Continuous two-axis control with AccelStepper
 * Hold ← → ↑ ↓ for motion, release to stop.
 * -------------------------------------------------------
 * X-axis : STEP = 2, DIR = 5, EN = 8
 * Y-axis : STEP = 3, DIR = 6, EN = 9
 */

#include <Arduino.h>
#include <AccelStepper.h>

// ── Pin assignments ───────────────────────────────────────
constexpr uint8_t STEP_X = 2, DIR_X = 5, EN_X = 8;
constexpr uint8_t STEP_Y = 3, DIR_Y = 6, EN_Y = 9;

// ── Motion parameters ─────────────────────────────────────
constexpr uint16_t MICRO_STEPS      = 4;           // A4988/DRV8825 jumpers
constexpr uint32_t STEPS_PER_REV    = 200UL * MICRO_STEPS;

constexpr float    MAX_SPEED_X      = 800.0;       // steps / s
constexpr float    ACCEL_X          = 400.0;       // steps / s²
constexpr float    MAX_SPEED_Y      = 1200.0;
constexpr float    ACCEL_Y          = 600.0;

// Big “infinite” distance for continuous travel
constexpr long     CONT_DIST        = 1000000L;    // steps

// ── Stepper objects ───────────────────────────────────────
AccelStepper stepperX(AccelStepper::DRIVER, STEP_X, DIR_X);
AccelStepper stepperY(AccelStepper::DRIVER, STEP_Y, DIR_Y);

inline void driversEnable(bool en) {
  digitalWrite(EN_X, en ? LOW : HIGH);   // LOW = enabled
  digitalWrite(EN_Y, en ? LOW : HIGH);
}

void setup() {
  pinMode(EN_X, OUTPUT); pinMode(EN_Y, OUTPUT);
  driversEnable(true);

  stepperX.setMaxSpeed(MAX_SPEED_X);
  stepperX.setAcceleration(ACCEL_X);
  stepperY.setMaxSpeed(MAX_SPEED_Y);
  stepperY.setAcceleration(ACCEL_Y);

  Serial.begin(115200);
  Serial.println(F("Stepper ready"));
}

/* ── Helper: start motion toward “infinity” ───────────────── */
inline void go(AccelStepper& s, int dir) {
  // keep target far ahead of current position
  s.moveTo(s.currentPosition() + dir * CONT_DIST);
}

/* ── Main loop ────────────────────────────────────────────── */
void loop() {
  if (Serial.available()) {
    switch (Serial.read()) {
      /*  X-axis  */
      case 'L':  go(stepperX, +1);      break;  // press ←
      case 'R':  go(stepperX, -1);      break;  // press →
      case 'l':  stepperX.stop();       break;  // release ← or →
      case 'r':  stepperX.stop();       break;

      /*  Y-axis  */
      case 'U':  go(stepperY, -1);      break;  // press ↑
      case 'D':  go(stepperY, +1);      break;  // press ↓
      case 'u':  stepperY.stop();       break;  // release ↑ or ↓
      case 'd':  stepperY.stop();       break;
    }
  }

  // keep steppers running / accelerating / decelerating
  stepperX.run();
  stepperY.run();
}
