#include <Arduino.h>
#include <AccelStepper.h>

/* =============================================================
   Dual-Axis Serial Jog Demo (AccelStepper version)
   -------------------------------------------------
   Keys over Serial:
     u / d  -> X axis +/- quarter turn
     r / l  -> Y axis +/- quarter turn
     U / D  -> X axis +/- full revolution
     R / L  -> Y axis +/- full revolution
     e      -> enable drivers (energize)
     E      -> disable drivers (de-energize)
     0      -> zero both axes (set currentPosition = 0)

   Behaviour:
   * Non-blocking: steppers accelerate/decelerate under library control.
   * Additional jog commands accumulate; each adds to the pending move.
   * Shared enable pin is handled manually because it drives both axes.

   Tune MAX_SPEED_STEPS_S & ACCEL_STEPS_S2 for your mechanics.
   ------------------------------------------------------------- */

/* -------- Pin assignment -------- */
/*  X-axis */
const uint8_t STEP_X = 2;   // STEP
const uint8_t DIR_X  = 5;   // DIR
/*  Y-axis */
const uint8_t STEP_Y = 3;   // STEP
const uint8_t DIR_Y  = 6;   // DIR

/* Enable (shared) */
const uint8_t EN_PIN = 8;   // ENABLE  (LOW = on, HIGH = off)

/* -------- Motion parameters -------- */
const long STEPS_PER_REV = 200L * 16L;          // match your driver\xE2\x80\x99s \xC2\xB5step mode

const long STEPS_PER_SCREEN_WIDTH  = 50L;       // was 1000L
const long STEPS_PER_SCREEN_HEIGHT = 50L;       // was 1000L
const long TURN  = STEPS_PER_SCREEN_HEIGHT;     // jog amount

/* User-tunable dynamic limits */
const float MAX_SPEED_STEPS_S = 800.0f * 32;  // steps/second
const float ACCEL_STEPS_S2    = 400.0f * 32;  // steps/second^2

/* -------- AccelStepper objects -------- */
// DRIVER interface = step + direction
AccelStepper stepperX(AccelStepper::DRIVER, STEP_X, DIR_X);
AccelStepper stepperY(AccelStepper::DRIVER, STEP_Y, DIR_Y);

/* -------- Enable helper -------- */
inline void enableDrivers(bool enable)
{
  // Active-LOW: LOW energizes both stepper drivers, HIGH releases.
  digitalWrite(EN_PIN, enable ? LOW : HIGH);
}

/* Convenience wrappers for jog moves ------------------------------------ */
inline void jogX(long steps) { stepperX.move(steps); }
inline void jogY(long steps) { stepperY.move(steps); }

/* -------- Arduino lifecycle -------- */
void setup()
{
  pinMode(EN_PIN, OUTPUT);
  enableDrivers(true);          // energize motors at startup

  // Configure dynamic limits.
  stepperX.setMaxSpeed(MAX_SPEED_STEPS_S / 2);
  stepperX.setAcceleration(ACCEL_STEPS_S2 / 2);
  stepperY.setMaxSpeed(MAX_SPEED_STEPS_S);
  stepperY.setAcceleration(ACCEL_STEPS_S2);

  Serial.begin(115200);
  Serial.println(F("AccelStepper dual-axis ready (u/d/r/l)."));
}

void loop()
{
  // Always service the steppers.
  stepperX.run();
  stepperY.run();

  // Process incoming serial jog commands (single char).
  if (Serial.available())
  {
    const char cmd = Serial.read();
    switch (cmd)
    {
      // X-axis (vertical)
      case 'u': jogX( TURN);  break; // \u2191
      case 'd': jogX(-TURN);  break; // \u2193

      // Y-axis (horizontal)
      case 'r': jogY( TURN);  break; // \u2192
      case 'l': jogY(-TURN);  break; // \u2190

      // optional: full-rev moves
      case 'U': jogX( STEPS_PER_REV);  break;
      case 'D': jogX(-STEPS_PER_REV);  break;
      case 'R': jogY( STEPS_PER_REV);  break;
      case 'L': jogY(-STEPS_PER_REV);  break;

      // enable / disable all drivers
      case 'e': enableDrivers(true);  Serial.println(F("Drivers enabled."));  break;
      case 'E': enableDrivers(false); Serial.println(F("Drivers disabled.")); break;

      // zero both axes
      case '0':
        stepperX.setCurrentPosition(0);
        stepperY.setCurrentPosition(0);
        Serial.println(F("Zeroed."));
        break;

      default:
        break; // ignore anything else
    }
  }
}

/* ---------------------- Notes & Tips ------------------------------------
   1. Accumulating vs. Absolute Jogging
      The jogX()/jogY() helpers above call move(), which *adds* steps to any
      already-in-progress move. If you want each keypress to represent a
      discrete move that cancels any previous remainder, use moveTo() with
      currentPosition()+steps.

   2. Shared ENABLE pin
      Because EN_PIN controls both drivers, it is handled manually here.

   3. Minimum STEP pulse width
      Some step/dir drivers need longer pulses; call setMinPulseWidth() if so.

   4. Units reminder
      setMaxSpeed() & setAcceleration() use steps as the distance unit.
   ----------------------------------------------------------------------- */
