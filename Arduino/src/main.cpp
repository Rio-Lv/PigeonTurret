#include <Arduino.h>
#include <AccelStepper.h>

/* =============================================================
   Dual‑Axis Serial Jog Demo (AccelStepper version)
   -------------------------------------------------
   Keys over Serial:
     u / d  -> X axis +/‑ quarter turn
     r / l  -> Y axis +/‑ quarter turn
     U / D  -> X axis +/‑ full revolution
     R / L  -> Y axis +/‑ full revolution
     e      -> enable drivers (energize)
     E      -> disable drivers (de‑energize)
     0      -> zero both axes (set currentPosition = 0)

   Behaviour:
   * Non‑blocking: steppers accelerate / decelerate under library control.
   * Additional jog commands accumulate; each adds to the pending move.
   * Shared enable pin is handled manually because it drives both axes.

   Tune MAX_SPEED_STEPS_S & ACCEL_STEPS_S2 for your mechanics.
   ------------------------------------------------------------- */

/* -------- Pin assignment -------- */
/*  X‑axis */
const uint8_t STEP_X = 2;   // STEP
const uint8_t DIR_X  = 5;   // DIR
/*  Y‑axis */
const uint8_t STEP_Y = 3;   // STEP
const uint8_t DIR_Y  = 6;   // DIR

/* Enable (shared) */
const uint8_t EN_PIN = 8;   // ENABLE  (LOW = on, HIGH = off)  <-- typical A4988/DRV8825

/* -------- Motion parameters -------- */
const long STEPS_PER_REV = 200L * 16L;          // match your driver’s µstep mode

const long STEPS_PER_SCREEN_WIDTH = 1000L;
const long STEPS_PER_SCREEN_HEIGHT = 1000L;
const long TURN  = STEPS_PER_SCREEN_HEIGHT; //

/* User‑tunable dynamic limits */
const float MAX_SPEED_STEPS_S = 800.0f * 32;  // steps / second (library float)
const float ACCEL_STEPS_S2    = 400.0f * 32;  // steps / second^2

/* -------- AccelStepper objects -------- */
// DRIVER interface = step + direction
AccelStepper stepperX(AccelStepper::DRIVER, STEP_X, DIR_X);
AccelStepper stepperY(AccelStepper::DRIVER, STEP_Y, DIR_Y);

/* -------- Enable helper -------- */
inline void enableDrivers(bool enable)
{
  // Active‑LOW: LOW energizes both stepper drivers, HIGH releases.
  digitalWrite(EN_PIN, enable ? LOW : HIGH);
}

/* Convenience wrappers for jog moves ------------------------------------ */
inline void jogX(long steps) { stepperX.move(steps); }
inline void jogY(long steps) { stepperY.move(steps); }

/* Optionally: if you prefer deterministic end‑positions (ignore queued
   distance), replace move() above with:
     stepperX.moveTo(stepperX.currentPosition() + steps);
   and same for Y.  See note in comments below. */

/* -------- Arduino lifecycle -------- */
void setup()
{
  pinMode(EN_PIN, OUTPUT);
  enableDrivers(true);          // energize motors at startup

  // Configure dynamic limits.
  stepperX.setMaxSpeed(MAX_SPEED_STEPS_S/2);
  stepperX.setAcceleration(ACCEL_STEPS_S2/2);
  stepperY.setMaxSpeed(MAX_SPEED_STEPS_S);
  stepperY.setAcceleration(ACCEL_STEPS_S2);

  Serial.begin(115200);
  /* Initial handshake message for host scripts. */
  Serial.println(F("Stepper ready"));
}

void loop()
{
  /* Always service the steppers. run() steps the motor toward its target
     position using the configured acceleration profile. It returns true
     while the motor is still running. */
  stepperX.run();
  stepperY.run();

  /* Process incoming serial jog commands (single char). */
  if (Serial.available())
  {
    const char cmd = Serial.read();
    switch (cmd)
    {
      /* X‑axis (vertical) */
      case 'u': jogX( TURN); break; // ↑
      case 'd': jogX(-TURN); break; // ↓

      /* Y‑axis (horizontal) */
      case 'r': jogY( TURN); break; // →
      case 'l': jogY(-TURN); break; // ←

      /* optional: full‑rev moves */
      case 'U': jogX( STEPS_PER_REV);  break;
      case 'D': jogX(-STEPS_PER_REV);  break;
      case 'R': jogY( STEPS_PER_REV);  break;
      case 'L': jogY(-STEPS_PER_REV);  break;

      /* enable / disable all drivers */
      case 'e': enableDrivers(true);  Serial.println(F("Drivers enabled."));  break;
      case 'E': enableDrivers(false); Serial.println(F("Drivers disabled.")); break;

      /* zero both axes */
      case '0':
        stepperX.setCurrentPosition(0);
        stepperY.setCurrentPosition(0);
        Serial.println(F("Zeroed."));
        break;

      default: /* ignore anything else */ break;
    }
  }
}

/* ---------------------- Notes & Tips ------------------------------------
   1. Accumulating vs. Absolute Jogging
      The jogX()/jogY() helpers above call move(), which *adds* steps to any
      already‑in‑progress move. This gives a smooth, buffered jog feel if you
      press keys quickly. If you want each keypress to represent a discrete
      move that cancels any previous remainder (closer to your blocking
      delay‑based sketch), change jogX/Y to use moveTo(currentPosition()+steps).

   2. Shared ENABLE pin
      Because EN_PIN controls *both* drivers, it is handled manually. If you
      prefer AccelStepper to manage enable (and you don’t mind both objects
      touching the same pin), you can do this *once* in setup(), e.g.:

          stepperX.setPinsInverted(false, false, true); // invert enable (active‑LOW)
          stepperX.setEnablePin(EN_PIN);
          stepperX.enableOutputs();
          // Do NOT also call setEnablePin() on stepperY; leave stepperY unmanaged.

      Then change enableDrivers() calls to stepperX.enableOutputs() /
      stepperX.disableOutputs().

   3. Minimum STEP pulse width
      Most step/dir drivers accept very short pulses; if yours needs longer
      (e.g., some TB6600 boards), call setMinPulseWidth(nMicros). Example:
          stepperX.setMinPulseWidth(20); // + approx 15 uS internal ≈ 35 uS total

   4. Units reminder
      setMaxSpeed() & setAcceleration() use *steps* as the distance unit. If
      you prefer rev/sec, multiply by STEPS_PER_REV.

   ----------------------------------------------------------------------- */
