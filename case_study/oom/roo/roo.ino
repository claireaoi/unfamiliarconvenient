// Unfamiliar Convenient
// Roo control v2.0
// Claire Glanois & Vytautas Jankauskas
// 2019—2020

/*
  
  Roomba comms based on Create2 library
  by Duncan Lilley and Susan Tuvell
  Works for Roomba Create 2 and domestic 600 Series
  Requires multiple hardware serial communications
  Arduino MEGA or similar
  Connect Roomba via Serial > 0 (all except from 
  the first one because it does not supply enough
  power

*/



#include <Create2.h>

// Instance to communicate with Roomba
Create2 roo(&Serial1, Create2::Baud19200);

// The pin attached to the Baud Rate Change pin
// on the DIN connector of the Roomba
const int BAUD_PIN = 5;

// Sensors
int chargingState;
int batteryCharge;
int batteryCapacity;

// Roomba states
bool cleaning = false;
bool docking = false;
bool charging = true;

// Timers
unsigned long currentMillis; 
unsigned long prevRegimeMillis;
unsigned long prevSensorMillis;

// Timer intervals
const int regimeCheckInterval = 900;
const int sensorCheckInterval = 15;  

//initialise position and angle, and the array containing all three
float myX=0;
float myY=0;
int myAngle=0;
  
void setup() {
  // Sets baud rate of Roomba to 19200
  roo.setBaudDefault(BAUD_PIN);
  delay(100);
  
  // For serial port monitoring via USB (debugging only)
  //Serial.begin(115200);
  //delay(100);

  // Bluetooth Module
  Serial3.begin(9600);
  delay(100);

  // Wake Roomba up
  Serial.println("Starting Roo");
  roo.start();
  delay(1000);

}

void loop() {
  // Make note of time
  currentMillis = millis();
  // Update which state Roo is in
  //checkRegime();
  // Update sensor data
  if (cleaning || docking || charging) { //! REMOVE CHARGING AFTER DEBUG
    processMovementSensors();
  }
}
