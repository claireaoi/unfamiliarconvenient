// Send Roomba's Coordinates to Python
void toPython() {
  if (currentMillis - prevSendMillis >= sendInterval) {
    String buf;
    buf += String(myX, 1);
    buf += F(";");
    buf += String(myY, 1);

    // Send buffer of Roomba's coordinates to Python
    Serial3.println(buf);
    Serial3.flush();
    // Send remaining battery to Python
    Serial3.println(batteryPercent)
    Serial3.flush();
          
    // Update send timer
    prevSendMillis += sendInterval;
  }
}
