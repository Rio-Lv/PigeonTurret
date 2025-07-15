/**
 * Two-axis stepper control (library-free, constant speed)
 * Serial command: "dx,dy,speed"
 * ------------------------------------------------------
 * X-axis: STEP = 2, DIR = 5, EN = 8
 * Y-axis: STEP = 3, DIR = 6, EN = 9
 */

#include <Arduino.h>

// ── Pin assignments ───────────────────────────────────────
constexpr uint8_t STEP_X = 2, DIR_X = 5, EN_X = 8;
constexpr uint8_t STEP_Y = 3, DIR_Y = 6, EN_Y = 9;

// ── Motion parameters ─────────────────────────────────────
constexpr float MAX_SPS_X = 1000.0;    // steps per second
constexpr float MAX_SPS_Y = 500.0;
constexpr float DEADZONE  = 0.05;     // ignore tiny commands

// ── State object ──────────────────────────────────────────
struct Axis {
  uint8_t  stepPin;
  uint8_t  dirPin;
  float    targetSPS;
  uint32_t intervalUs;
  uint32_t lastStepUs;

  /*–– constructor –––––––––––––––––––––––––––––––––––––––*/
  Axis(uint8_t step, uint8_t dir)
    : stepPin(step), dirPin(dir),
      targetSPS(0), intervalUs(0), lastStepUs(0) {}
};

Axis X(STEP_X, DIR_X);     // now compiles everywhere ✔
Axis Y(STEP_Y, DIR_Y);

// Global speed scale
float speedFactor = 1.0;

// ── Helper functions ─────────────────────────────────────
inline void enableDrivers(bool on) {
  digitalWrite(EN_X, on ? LOW : HIGH);
  digitalWrite(EN_Y, on ? LOW : HIGH);
}

void applyCommand(float dx, float dy, float speed) {
  // Dead-zone & clamp
  if (fabs(dx) < DEADZONE) dx = 0;
  if (fabs(dy) < DEADZONE) dy = 0;
  dx = constrain(dx, -1.0, 1.0);
  dy = constrain(dy, -1.0, 1.0);
  speedFactor = constrain(speed, 0.1, 1.0);

  X.targetSPS = dx * MAX_SPS_X * speedFactor;
  Y.targetSPS = dy * MAX_SPS_Y * speedFactor;

  X.intervalUs = (X.targetSPS == 0) ? 0 : (1e6 / fabs(X.targetSPS));
  Y.intervalUs = (Y.targetSPS == 0) ? 0 : (1e6 / fabs(Y.targetSPS));

  digitalWrite(X.dirPin, (X.targetSPS >= 0) ? HIGH : LOW);
  digitalWrite(Y.dirPin, (Y.targetSPS >= 0) ? HIGH : LOW);

//   Serial.print("Set: ");
//   Serial.print(X.targetSPS); Serial.print(" sps X, ");
//   Serial.print(Y.targetSPS); Serial.println(" sps Y");
}

void stepAxis(Axis &a) {
  if (a.intervalUs == 0) return;             // stopped
  uint32_t now = micros();
  if (now - a.lastStepUs >= a.intervalUs) {
    a.lastStepUs = now;
    digitalWrite(a.stepPin, HIGH);
    delayMicroseconds(2);
    digitalWrite(a.stepPin, LOW);
  }
}

void setup() {
  pinMode(STEP_X, OUTPUT);  pinMode(DIR_X, OUTPUT);  pinMode(EN_X, OUTPUT);
  pinMode(STEP_Y, OUTPUT);  pinMode(DIR_Y, OUTPUT);  pinMode(EN_Y, OUTPUT);
  enableDrivers(true);

  Serial.begin(115200);
  while (!Serial);
  Serial.println(F("Simple stepper controller ready — cmd: dx,dy,speed"));
}

void loop() {
  /* ---------- Serial input ---------- */
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    if (cmd.length()) {
      char buf[32];
      cmd.toCharArray(buf, sizeof(buf));
      float dx  = atof(strtok(buf, ","));
      char *tok = strtok(NULL, ",");
      if (!tok) return;
      float dy  = atof(tok);
      tok = strtok(NULL, ",");
      float spd = tok ? atof(tok) : speedFactor;
      applyCommand(dx, dy, spd);
    }
  }

  /* ---------- Motor stepping ---------- */
  stepAxis(X);
  stepAxis(Y);
}
