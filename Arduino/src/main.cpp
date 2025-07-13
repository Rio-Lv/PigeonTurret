/**
 * Smooth two-axis stepper control with numeric velocity input
 * Accepts commands in format: "dx,dy,speed"
 * Example: "0.5,-0.3,0.8" = 50% right, 30% down at 80% speed
 * ----------------------------------------------------------
 * X-axis: STEP = 2, DIR = 5, EN = 8
 * Y-axis: STEP = 3, DIR = 6, EN = 9
 */

#include <Arduino.h>
#include <AccelStepper.h>

// ── Pin assignments ───────────────────────────────────────
constexpr uint8_t STEP_X = 2, DIR_X = 5, EN_X = 8;
constexpr uint8_t STEP_Y = 3, DIR_Y = 6, EN_Y = 9;

// ── Motion parameters ─────────────────────────────────────
constexpr uint16_t MICRO_STEPS = 4;
constexpr uint32_t STEPS_PER_REV = 200UL * MICRO_STEPS;

// Base speeds (steps/sec)
constexpr float MAX_SPEED_X = 800.0;
constexpr float MAX_SPEED_Y = 1200.0;

// Acceleration (steps/sec²)
constexpr float ACCEL_X = 1200.0;
constexpr float ACCEL_Y = 1800.0;

// Deadzone to prevent micro-jitters
constexpr float DEADZONE = 0.05;

// ── Stepper objects ───────────────────────────────────────
AccelStepper stepperX(AccelStepper::DRIVER, STEP_X, DIR_X);
AccelStepper stepperY(AccelStepper::DRIVER, STEP_Y, DIR_Y);

// Command parsing
const uint8_t COMMAND_BUFFER_SIZE = 32;
char commandBuffer[COMMAND_BUFFER_SIZE];
uint8_t bufferIndex = 0;

// Velocity targets (-1.0 to 1.0)
float targetVelX = 0;
float targetVelY = 0;
float speedFactor = 1.0; // Global speed multiplier

// Debugging
unsigned long lastDebugTime = 0;
const unsigned long DEBUG_INTERVAL = 1000; // ms

inline void driversEnable(bool en)
{
    digitalWrite(EN_X, en ? LOW : HIGH);
    digitalWrite(EN_Y, en ? LOW : HIGH);
}

void setup()
{
    pinMode(EN_X, OUTPUT);
    pinMode(EN_Y, OUTPUT);
    driversEnable(true);

    // Configure steppers with smooth acceleration
    stepperX.setMaxSpeed(MAX_SPEED_X);
    stepperX.setAcceleration(ACCEL_X);
    stepperX.setCurrentPosition(0); // Reset position

    stepperY.setMaxSpeed(MAX_SPEED_Y);
    stepperY.setAcceleration(ACCEL_Y);
    stepperY.setCurrentPosition(0); // Reset position

    Serial.begin(115200);
    while (!Serial)
        ; // Wait for serial to initialize
    Serial.println(F("Stepper controller ready"));
    Serial.println(F("Send commands as: dx,dy,speed"));
}

// Custom float parser for Arduino AVR compatibility
float parseFloat(char *str, char **endPtr)
{
    float result = 0.0;
    bool negative = false;
    float fraction = 1.0;
    bool hasFraction = false;
    uint8_t decimalPlaces = 0;

    // Skip leading whitespace
    while (*str == ' ')
        str++;

    // Handle sign
    if (*str == '-')
    {
        negative = true;
        str++;
    }
    else if (*str == '+')
    {
        str++;
    }

    // Parse integer part
    while (*str >= '0' && *str <= '9')
    {
        result = result * 10.0 + (*str - '0');
        str++;
    }

    // Parse fractional part
    if (*str == '.')
    {
        hasFraction = true;
        str++;
        while (*str >= '0' && *str <= '9')
        {
            result = result * 10.0 + (*str - '0');
            fraction *= 10.0;
            decimalPlaces++;
            str++;
        }
    }

    // Apply fraction scaling
    if (hasFraction)
    {
        result /= fraction;
    }

    // Apply sign
    if (negative)
    {
        result = -result;
    }

    // Set end pointer
    if (endPtr != NULL)
    {
        *endPtr = str;
    }

    return result;
}

// Parse incoming velocity commands
// Parse incoming velocity commands
void parseCommand(const char *command)
{
    char buffer[COMMAND_BUFFER_SIZE];
    strncpy(buffer, command, COMMAND_BUFFER_SIZE);
    buffer[COMMAND_BUFFER_SIZE - 1] = '\0'; // Ensure null-terminated

    char *token = strtok(buffer, ",");
    if (!token)
        return;
    targetVelX = atof(token);

    token = strtok(NULL, ",");
    if (!token)
        return;
    targetVelY = atof(token);

    token = strtok(NULL, ",");
    if (token)
    {
        speedFactor = atof(token);
        speedFactor = constrain(speedFactor, 0.1, 1.0);
    }

    // Apply deadzone to prevent micro-jitters
    if (fabs(targetVelX) < DEADZONE)
        targetVelX = 0;
    if (fabs(targetVelY) < DEADZONE)
        targetVelY = 0;

    // Apply speed limits
    float velX = constrain(targetVelX, -1.0, 1.0) * speedFactor;
    float velY = constrain(targetVelY, -1.0, 1.0) * speedFactor;

    // Calculate actual speeds
    float actualSpeedX = velX * MAX_SPEED_X;
    float actualSpeedY = velY * MAX_SPEED_Y;

    // Set new speeds with acceleration control
    stepperX.setSpeed(actualSpeedX);
    stepperY.setSpeed(actualSpeedY);

    // Debug output
    Serial.print("Command: ");
    Serial.print(velX);
    Serial.print(", ");
    Serial.print(velY);
    Serial.print(", ");
    Serial.print(speedFactor);
    Serial.print(" -> ");
    Serial.print(actualSpeedX);
    Serial.print(" sps X, ");
    Serial.print(actualSpeedY);
    Serial.println(" sps Y");
}
void loop()
{
    // Read serial commands
    while (Serial.available())
    {
        char c = Serial.read();

        if (c == '\n' || c == '\r')
        {
            if (bufferIndex > 0)
            {
                commandBuffer[bufferIndex] = '\0'; // Null-terminate
                parseCommand(commandBuffer);
                bufferIndex = 0;
            }
        }
        else if (bufferIndex < COMMAND_BUFFER_SIZE - 1)
        {
            commandBuffer[bufferIndex++] = c;
        }
    }

    // Run steppers with acceleration control
    stepperX.run();
    stepperY.run();

    // Periodic debugging
    if (millis() - lastDebugTime > DEBUG_INTERVAL)
    {
        Serial.print(F("Position: X="));
        Serial.print(stepperX.currentPosition());
        Serial.print(F(" Y="));
        Serial.print(stepperY.currentPosition());
        Serial.print(F(" Speed: X="));
        Serial.print(stepperX.speed());
        Serial.print(F(" Y="));
        Serial.println(stepperY.speed());

        lastDebugTime = millis();
    }
}