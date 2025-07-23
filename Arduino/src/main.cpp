#include <Arduino.h>
#include <AccelStepper.h>
#include <ArduinoJson.h>

/* =============================================================
   Dual-Axis Acknowledgment Demo
   -------------------------------------------------
   Accepts absolute coordinates and sends "done" upon completion.

   Behaviour:
   * Ignores new commands while a move is in progress.
   * Sends a "done\n" message over serial when a move is complete.
   ------------------------------------------------------------- */

/* -------- Pin assignment & Gearing -------- */
const uint8_t STEP_X = 2;
const uint8_t DIR_X  = 5;
const uint8_t STEP_Y = 3;
const uint8_t DIR_Y  = 6;
const uint8_t EN_PIN = 8;
const float GEAR_RATIO_X = 1.0f / 4.0f;

/* -------- Motion parameters -------- */
const float MAX_SPEED_STEPS_S = 800.0f * 32;
const float ACCEL_STEPS_S2    = 400.0f * 32;

/* -------- AccelStepper objects -------- */
AccelStepper stepperX(AccelStepper::DRIVER, STEP_X, DIR_X);
AccelStepper stepperY(AccelStepper::DRIVER, STEP_Y, DIR_Y);

// NEW: State variable to track if motors are busy
bool isMoving = false;

/* -------- Arduino lifecycle -------- */
void setup()
{
  pinMode(EN_PIN, OUTPUT);
  digitalWrite(EN_PIN, LOW);

  stepperX.setMaxSpeed(MAX_SPEED_STEPS_S * GEAR_RATIO_X);
  stepperX.setAcceleration(ACCEL_STEPS_S2 * GEAR_RATIO_X);
  stepperY.setMaxSpeed(MAX_SPEED_STEPS_S);
  stepperY.setAcceleration(ACCEL_STEPS_S2);

  stepperX.setCurrentPosition(0);
  stepperY.setCurrentPosition(0);

  Serial.begin(115200);

  Serial.println(F("Arduino ready. Waiting for commands..."));

}

void loop()
{
  // These MUST always run to step the motors
  stepperX.run();
  stepperY.run();

  // --- State Machine Logic ---

  // If we are currently executing a move, check if it's finished.
  if (isMoving) {
    // A move is complete when both motors have 0 steps left to go.
    if (stepperX.distanceToGo() == 0 && stepperY.distanceToGo() == 0) {
      isMoving = false;
      Serial.println("done"); // Send acknowledgment to Python
    }
  }
  // Otherwise, if we are idle, check for a new command.
  else {
    if (Serial.available() > 0) {
      StaticJsonDocument<96> doc;
      DeserializationError error = deserializeJson(doc, Serial);

      if (error) {
        Serial.print(F("deserializeJson() failed: "));
        Serial.println(error.f_str());
        while(Serial.available() > 0) Serial.read();
        return;
      }

      bool commanded = false;
      if (doc.containsKey("x")) {
        long targetX = doc["x"];
        stepperX.moveTo(targetX * GEAR_RATIO_X);
        commanded = true;
      }
      if (doc.containsKey("y")) {
        stepperY.moveTo(doc["y"]);
        commanded = true;
      }

      // If a valid move was commanded, set our state to moving.
      if (commanded) {
        isMoving = true;
      }
    }
  }
}