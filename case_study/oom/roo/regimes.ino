void checkRegime() {
  if (currentMillis - prevRegimeMillis >= regimeCheckInterval) {
    bool batteryState = batteryLow();
    
    if (!cleaning && !batteryState && !charging) {
      
      // start cleaning
      roo.clean();

      cleaning = true;
      docking = false;
      charging = false;
    }

    else if (!docking && cleaning && batteryState) {
      roo.seekDock();

      cleaning = false;
      docking = true;
      charging = false;
    }
 
    else {
      // change to true after debugging
      if (!batteryCharging()) {
        cleaning = false;
        docking = false;
        charging = true;
  
        // Wait for CS1's green light
        if (!batteryState) {
          callPython();
        }
      }      
    }
    
    // Update timer
    prevRegimeMillis += regimeCheckInterval;
  }
}

void callPython() {
  //Serial3.println("ready"); // tell Python to call
  //Serial3.flush();

  // This needs work !!
  if (Serial3.available() > 0) {
    int message = 0;
    String s = Serial3.readString();
    // Serial.println("Message from Python: " + s);
    message = s.toInt();
    if (message == 1) {
      charging = false;
      Serial3.println("busy"); // tell Python to call
      Serial3.flush();
      }
  }
}
