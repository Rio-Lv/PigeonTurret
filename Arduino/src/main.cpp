#include <Arduino.h>
#include <AccelStepper.h>
#include <ArduinoJson.h>

/* =============================================================
   Dual-Axis Acknowledgment Demo (with Power-Saving)
   -------------------------------------------------
   Accepts absolute coordinates and sends "done" upon completion.

   Behaviour:
   * Disables motors after a period of inactivity to save power.
   * Automatically re-enables motors when a new command is received.
   ------------------------------------------------------------- */

// NEW: Configuration for the power-saving timer
const unsigned long INACTIVITY_TIMEOUT_MS = 4000; // 4 seconds

/* -------- Pin assignment & Gearing -------- */
const uint8_t STEP_X = 2;
const uint8_t DIR_X  = 5;
const uint8_t STEP_Y = 3;
const uint8_t DIR_Y  = 6;
const uint8_t EN_PIN = 8; // Assumes LOW=on, HIGH=off
const float GEAR_RATIO_X = 48.0f / 20.0f;

/* -------- Motion parameters -------- */
const float MAX_SPEED_STEPS_S = 800.0f * 4;
const float ACCEL_STEPS_S2    = 400.0f * 4;

/* -------- AccelStepper objects -------- */
AccelStepper stepperX(AccelStepper::DRIVER, STEP_X, DIR_X);
AccelStepper stepperY(AccelStepper::DRIVER, STEP_Y, DIR_Y);

/* -------- State Variables -------- */
bool isMoving = false;
// NEW: Variables for tracking motor power state and activity
bool motorsEnabled = true;
unsigned long lastActivityTime = 0;

// NEW: Helper function to disable motor drivers
void disableMotors() {
  digitalWrite(EN_PIN, HIGH); // Set HIGH to disable most common drivers
  motorsEnabled = false;
  // Serial.println(F("Motors disabled due to inactivity.")); // Optional debug message
}

// NEW: Helper function to enable motor drivers
void enableMotors() {
  digitalWrite(EN_PIN, LOW); // Set LOW to enable
  motorsEnabled = true;
  // Serial.println(F("Motors enabled.")); // Optional debug message
}

/* -------- Arduino lifecycle -------- */
void setup() {
  pinMode(EN_PIN, OUTPUT);
  enableMotors(); // Ensure motors are enabled on startup

  stepperX.setMaxSpeed(MAX_SPEED_STEPS_S * GEAR_RATIO_X);
  stepperX.setAcceleration(ACCEL_STEPS_S2 * GEAR_RATIO_X);
  stepperY.setMaxSpeed(MAX_SPEED_STEPS_S);
  stepperY.setAcceleration(ACCEL_STEPS_S2);

  stepperX.setCurrentPosition(0);
  stepperY.setCurrentPosition(0);

  Serial.begin(115200);
  Serial.println(F("Arduino ready. Waiting for commands..."));

  // NEW: Initialize the activity timer
  lastActivityTime = millis();
}

void loop() {
  // These MUST always run to step the motors
  stepperX.run();
  stepperY.run();

  // --- State Machine Logic ---

  if (isMoving) {
    // We are active, so reset the timer
    lastActivityTime = millis();
    // Check if the move is finished
    if (stepperX.distanceToGo() == 0 && stepperY.distanceToGo() == 0) {
      isMoving = false;
      lastActivityTime = millis(); // Reset timer one last time when move completes
      Serial.println("done");
    }
  } else { // Not moving, check for new commands or timeout
    // Check for a new command
    if (Serial.available() > 0) {
      // NEW: A command is arriving, so re-enable motors if they were off
      if (!motorsEnabled) {
        enableMotors();
        // Give drivers a moment to stabilize before moving. 10ms is generous.
        delay(10); 
      }
      
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

      if (commanded) {
        isMoving = true;
        // NEW: Reset the activity timer since we just got a new command
        lastActivityTime = millis();
      }
    }

    // NEW: Check for inactivity timeout if motors are enabled and we are not moving
    if (motorsEnabled && !isMoving) {
      if (millis() - lastActivityTime > INACTIVITY_TIMEOUT_MS) {
        disableMotors();
      }
    }
  }
}