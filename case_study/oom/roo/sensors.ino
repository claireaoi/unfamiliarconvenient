// Get "Distance" and "Angle" sensor data from Roo then send to CS1
void processMovementSensors() {
  if (currentMillis - prevSensorMillis >= sensorCheckInterval) {
    // Ask for Distance and Angle Data
    uint8_t sensorData[26];
    roo.sensors(Create2::Sensors7to26, sensorData, 26);

    chargingState = sensorData[16]; 
    batteryCharge = (sensorData[22]<<8) | sensorData[23];
    batteryCapacity = (sensorData[24]<<8) | sensorData[25];

    int distance = (sensorData[12]<<8) | sensorData[13];
    int angle = (sensorData[14]<<8) | sensorData[15];

    //compute new angle, in degrees
    myAngle += angle;
    myAngle = myAngle % 360;
    
    // compute new position myX, myY
    myX += -distance*sin(PI * myAngle /180);
    myY += distance*cos(PI * myAngle /180);
    
    // Update sensor timer
    prevSensorMillis += sensorCheckInterval;
  }
}


// Check if battery is sufficiently charged
bool batteryLow() {
  batteryPercent = map(batteryCharge, 0, batteryCapacity, 0, 100);
  if (batteryPercent < 10) {
    return true;
    }
  else {
    return false;
  }
}

// Check if battery is Charging
bool batteryCharging() {
  if (chargingState != 0) {
    return true;
  }
  else {
    return false;
  }
}

// GPS Data
void getClearestSNR(int &satNum, int &satSNR) { // pass addresses
  for (int i=0; i<4; ++i) {
    int no = atoi(satNumber[i].value());
    if (no >= 1 && no <= MAX_SATELLITES) {
          sats[no-1].snr = atoi(snr[i].value());
          sats[no-1].active = true;
    }
  }
      
  int totalMessages = atoi(totalGPGSVMessages.value());
  int currentMessage = atoi(messageNumber.value());
  //int inView = atoi(satsInView.value());

  // initalize as empty
  satNum=0;
  satSNR=0;
  int maximum = 0;
  
  if (totalMessages == currentMessage) {
    //Serial.print(F("Sats in View=")); Serial.println(atoi(satsInView.value())); // for debugging
    for (int i=0; i<MAX_SATELLITES; ++i) {
        if (sats[i].active) {
           if (sats[i].snr >= 30 && maximum < sats[i].snr) { // get clearest snr
             satNum=i+1;
             satSNR=sats[i].snr;
             maximum=satSNR;
           }
        }
    }

    for (int i=0; i<MAX_SATELLITES; ++i) {
       sats[i].active = false;
    }
  }
}
