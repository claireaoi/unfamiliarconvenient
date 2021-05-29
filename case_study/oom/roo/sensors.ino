// Get "Distance" and "Angle" sensor data from Roo then send to CS1
void processMovementSensors(myData) {
  if (currentMillis - prevSensorMillis >= sensorCheckInterval) {
    // Ask for Distance and Angle Data
    uint8_t sensorData[26];
    roo.sensors(Create2::Sensors7to26, sensorData, 26);

    chargingState = sensorData[16]; 
    batteryCharge = (sensorData[22]<<8) | sensorData[23];
    batteryCapacity = (sensorData[24]<<8) | sensorData[25];

    int distance = (sensorData[12]<<8) | sensorData[13];
    int angle = (sensorData[14]<<8) | sensorData[15];

    // =========================================
    // ADD THE ANGLE, DISTANCE CALCULATIONS HERE
    // =========================================
    //compute new angle, in degree
    myAngle += angle
    myAngle= myAngle % 360
    //compute new position myX, myY
    myX += -distance*sin(PI * myAngle /180)
    myY += distance*cos(PI * myAngle /180)]
    
    // Update sensor timer
    prevSensorMillis += sensorCheckInterval;
  }
}



// Check if battery is sufficiently charged
bool batteryLow() {
  int batteryPercent = map(batteryCharge, 0, batteryCapacity, 0, 100);
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
