#include <Arduino.h>

/* -------- Pin assignment -------- */
/*  X‑axis */
const int stepX = 2;   // STEP
const int dirX  = 5;   // DIR
/*  Y‑axis */
const int stepY = 3;   // STEP
const int dirY  = 6;   // DIR

/* Enable (shared) */
const int enPin = 8;   // ENABLE  (LOW = on, HIGH = off)

/* -------- Motion parameters -------- */
const int stepDelay = 400;               // µs between rising edges
const int stepsPerRev = 200 * 8;         // match your driver’s µstep mode
const int quarterTurn = stepsPerRev / 4; // 90° move

/* -------- Helper functions -------- */
void singleStep(int stepPin)
{
  digitalWrite(stepPin, HIGH);
  delayMicroseconds(stepDelay);
  digitalWrite(stepPin, LOW);
  delayMicroseconds(stepDelay);
}

void rotateSteps(int stepPin, int dirPin, int steps, bool clockwise)
{
  digitalWrite(dirPin, clockwise ? HIGH : LOW);
  for (int i = 0; i < steps; ++i) singleStep(stepPin);
}

/* -------- Arduino lifecycle -------- */
void setup()
{
  pinMode(stepX, OUTPUT);
  pinMode(dirX,  OUTPUT);
  pinMode(stepY, OUTPUT);
  pinMode(dirY,  OUTPUT);
  pinMode(enPin, OUTPUT);

  digitalWrite(enPin, LOW);   // enable both drivers

  Serial.begin(115200);
  Serial.println(F("Stepper ready"));
}

void loop()
{
  if (!Serial.available()) return;

  char cmd = Serial.read();
  switch (cmd)
  {
    /* X‑axis (vertical) */
    case 'u': rotateSteps(stepX, dirX, quarterTurn, true ); break; // ↑
    case 'd': rotateSteps(stepX, dirX, quarterTurn, false); break; // ↓

    /* Y‑axis (horizontal) */
    case 'r': rotateSteps(stepY, dirY, quarterTurn, true ); break; // →
    case 'l': rotateSteps(stepY, dirY, quarterTurn, false); break; // ←

    /* optional: full‑rev moves, jogs, etc.
       case 'U': rotateSteps(stepX, dirX, stepsPerRev, true ); break;
       case 'D': rotateSteps(stepX, dirX, stepsPerRev, false); break;
    */
    default: /* ignore anything else */ break;
  }
}
