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

#include <TinyGPS++.h>
#include <Create2.h>

// Instance to communicate with Roomba
Create2 roo(&Serial2, Create2::Baud19200);

// Instance for the GPS module
static const int MAX_SATELLITES = 40;
TinyGPSPlus gps;
TinyGPSCustom totalGPGSVMessages(gps, "GPGSV", 1); // $GPGSV sentence, first element
TinyGPSCustom messageNumber(gps, "GPGSV", 2);      // $GPGSV sentence, second element
TinyGPSCustom satsInView(gps, "GPGSV", 3);         // $GPGSV sentence, third element
TinyGPSCustom satNumber[4]; 
TinyGPSCustom snr[4];

static const uint32_t GPSBaud = 9600;
bool gpsCaptured = false;
int satNum = 0;
int clearSNR = 0;

// Satellite struct
struct
{
  bool active;
  int snr;
} sats[MAX_SATELLITES];

// The pin attached to the Baud Rate Change pin
// on the DIN connector of the Roomba
const int BAUD_PIN = 5;

// Sensors
int chargingState;
int batteryCharge;
int batteryCapacity;
int batteryPercent; 

// Roomba states
bool cleaning = false;
bool docking = false;
bool charging = true;

// Timers
unsigned long currentMillis; 
unsigned long prevRegimeMillis;
unsigned long prevSensorMillis;
unsigned long prevSendMillis;

// Timer intervals
const int sendInterval = 752;
const int regimeCheckInterval = 1001;
const int sensorCheckInterval = 34;  

//Position and angle
float myX=0;
float myY=0;
int myAngle=0;
  
void setup() {
  // Sets baud rate of Roomba to 19200
  roo.setBaudDefault(BAUD_PIN);
  delay(150);
  
  // For serial port monitoring via USB (debugging only)
  Serial.begin(115200);
  delay(100);

  // GPS module
  Serial1.begin(9600);
  Serial1.begin(GPSBaud);

  // Initalize TinyGPSCustom objects at appropriate offsets
  for (int i=0;i<4;++i) {
    satNumber[i].begin(gps, "GPGSV", 4 + 4 * i); // offsets 4, 8, 12, 16
    snr[i].begin(      gps, "GPGSV", 7 + 4 * i); // offsets 7, 11, 15, 19
  }
  
  // Bluetooth Module
  Serial3.begin(9600);
  delay(150);

  // Wake Roomba up
  Serial3.println("starting roo");
  Serial3.flush();
  
  roo.start();
  delay(1000);

}

void loop() {
  // Make note of time
  currentMillis = millis();

  // Capture GPS Data, constantly
  while (Serial1.available() > 0 && !gpsCaptured){
    gps.encode(Serial1.read());

    if (totalGPGSVMessages.isUpdated()) {
       satNum = 0;
       clearSNR = 0;
       getClearestSNR(satNum, clearSNR);
       if (clearSNR != 0 && satNum != 0) {
          gpsCaptured = true; // captured valid gps data
       }
    }
  }
  
  // Update which state Roo is in
  checkRegime();

  // HERE IMPLEMENT MESSAGE FROM PYTHON TO START/STOP ROO REMOTELY
  
  // Update Roomba sensor data
  // if gpsCaptured, then roo must begin
  if (cleaning || docking) { // || charging ! REMOVE CHARGING AFTER DEBUG
    processMovementSensors();
    toPython();
    //gpsCaptured = false;
  }
}
