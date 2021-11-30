// Copyright Model B, LLC 2017.
// Author: J. Simmons 
// https://opendesignengine.net/projects/holoseat/
// 
// This file is part of the Holoseat software suite (firmware, control software, etc).
//
// The Holoseat software suite is free software: you can redistribute it and/or modify 
// it under the terms of the GNU General Public License as published by the Free Software 
// Foundation, either version 3 of the License, or (at your option) any later version.
//
// Holoseat software suite is distributed in the hope that it will be useful, but 
// WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or 
// FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License along with Holoseat 
// software suite.  If not, see <http://www.gnu.org/licenses/>.

//
// Holoseat Firmware
// This firmware detects the cadence and direction of an exercise bike or eliptical machine 
// and when the cadence is greater than a trigger value sends the specified key to trigger 
// walking forward (w) or backward (s) as needed in video games such as FPSs, RPGs, and MMOs.
//
// The process for calculating cadence is to measure the time difference (deltaT) between
// sensor events on the primary sensor.  We then calculate the cadence from deltaT since we
// know a single revolution has occurred during the time measured as deltaT. 
//
// The process for determining the direction of the pedalling is to measure the time between 
// sensor events on sensors 1 and 2.  We record both the time from sensor 1 to 2 (SensedDirectionT2) 
// and the time from sensor 2 to 1 (SensedDirectionT1).  If SensedDirectionT1 is greater than 
// SensedDirectionT2, then the user is pedalling forward, otherwise the user is pedalling
// backward.

 //#define DEBUG

#include "holoseat-constants.h"  // contains holoseat configuration settings
#include "Keyboard.h"            // for sending the walk keys
#include "math.h"                // ??
#include <Bounce2.h>             // for debouncing the enable button
#include <ArduinoJson.h>         // for using JSON as input and output

// version strings
char FirmwareVersionString[] = "v0.4.0";
char HspVersionString[] = "v0.4.0";
char Hardware_v0_4_VersionString[] = "v0.4";
char Hardware_v1_0_VersionString[] = "v1.0";

// set up ArduinoJSON
const char Error_Illegal_Verb[] = "Illegal VERB";

// Parameter values from holoseat_constants.h
char WalkForwardCharacter = DefaultWalkForwardCharacter;
char WalkBackwardCharacter = DefaultWalkBackwardCharacter;
unsigned int BaseTriggerCadence = 25;       // first interval for trigger cadence
unsigned int TriggerCadenceThreshold = 5;   // number of RPM above trigger cadence to step up
unsigned int CurrentTriggerCadence = BaseTriggerCadence;
//unsigned int ForwardTriggerCadence = DefaultTriggerCadence;
//unsigned int BackwardTriggerCadence = DefaultTriggerCadence;
unsigned int LoggingEnabled = DefaultLoggingEnabled;
unsigned int LoggingInterval = DefaultLoggingInterval;

// when we wake up, we will go through the transition right away, so set up for that fact
unsigned int HoloseatEnabled = !DefaultHoloseatEnabled;  

// Track key board state
char CurrentPressedKey = 0;       // what is the current key being pressed, 0 means no key pressed
char DesiredPressedKey = 0;       // what key does the user want pressed, 0 means no key

// calculated values
float Cadence;                    // pedalling speed
volatile float SensedDeltaT;      // deltaT as calculated during interrupt calls
volatile boolean WalkingForward;  // walking direction
volatile boolean StepTriggered;   // have we had an unhandled step event?

// sensor data and functions
const int CadencePin = 3;                         // pin used to measure cadence
const int DirectionPin = 2;                       // pin to read direction
const int NumPoles = 12;                          // number of magnetic pole pairs on the tone ring
volatile unsigned long LastStepTime;              // last time the step sensor was triggered

// common function to attach/detach interrupts
void EnableSensors(unsigned int enable) {
  if (enable) {
    attachInterrupt(digitalPinToInterrupt(CadencePin), DetectCadence, FALLING);
  }
  else {
    detachInterrupt(digitalPinToInterrupt(CadencePin));
  }
}

// interrupt function for sensor 1, used to measure cadence
void DetectCadence() {
  unsigned long currentTime = millis();
  SensedDeltaT = (currentTime - LastStepTime);
  LastStepTime = currentTime;
  WalkingForward = digitalRead(DirectionPin);  // CCW is forward
  StepTriggered = true;
}

// Logging data
volatile unsigned long LastLogTime;   // time since last log message was sent

// formats status string and sends to serial connection if available
// see https://opendesignengine.net/projects/holoseat/wiki/Software_Source_Code#HoloSeat-Serial-Protocol
// deprecated
void SendStateMessage_old() {
  if(!Serial) // if the serial port connection is not available, skip state message
    return;
  
  Serial.print(FirmwareVersionString);
  Serial.print(",");
  Serial.print(WalkForwardCharacter);
  Serial.print("(");
  Serial.print(DefaultWalkForwardCharacter);
  Serial.print("),");
  Serial.print(WalkBackwardCharacter);
  Serial.print("(");
  Serial.print(DefaultWalkBackwardCharacter);
  Serial.print("),");
  Serial.print(HoloseatEnabled);
  Serial.print("(");
  Serial.print(DefaultHoloseatEnabled);
  Serial.print("),");
  if (!WalkingForward)
    Serial.print("-");
  Serial.print(round(Cadence));
  Serial.print("/");
  Serial.print(CurrentTriggerCadence);
  Serial.print("(");
  //Serial.print(DefaultTriggerCadence);
  Serial.print(0);
  Serial.print("),");
  Serial.print(LoggingEnabled);
  Serial.print("(");
  Serial.print(DefaultLoggingEnabled);
  Serial.print(")/");
  Serial.print(LoggingInterval);
  Serial.print("(");
  Serial.print(DefaultLoggingInterval);
  Serial.println(")");
}

void SendStateMessage() {
  const size_t bufferSize = JSON_OBJECT_SIZE(2);
  DynamicJsonBuffer jsonBuffer(bufferSize);
  JsonObject& root = jsonBuffer.createObject();

  root["messageId"] = "";  
  root["StateMessage"] = "Holoseat stating";
  root.printTo(Serial);
  Serial.println();
}

char* GetHardwareVersion() {
  // TODO - add actual calls to hardware to determine HW version
  return Hardware_v0_4_VersionString;
}

void SerialReturnError(char* messageId, char* errorMessage) {
  const size_t bufferSize = JSON_OBJECT_SIZE(2);
  DynamicJsonBuffer jsonBuffer(bufferSize);
  JsonObject& root = jsonBuffer.createObject();

  root["messageId"] = messageId;  
  root["Error"] = errorMessage;
  root.printTo(Serial);
  Serial.println();
}

// Parses commands from serial connection
// see https://opendesignengine.net/projects/holoseat/wiki/HSP
void ProcessSerialData() {
  if (Serial && Serial.available()) {
    DynamicJsonBuffer jsonBuffer(1024);
    JsonObject& root = jsonBuffer.parse(Serial);

     if (!root.success()) {
      Serial.println("{\"Error\":\"JSON Parsing Failed\"}");
      return;
    }

    // get the messageId, uri, and verb
    const char* messageId = root["messageId"];
    const char* uri = root["uri"];
    const char* verb = root["verb"];

    // find the method for uri/verb pair
    if (strcmp(uri, "/lowlevel/events") == 0) {
      if (strcmp(verb, "GET") == 0) {
        LowlevelEventsGet(messageId);
      }
      else {
        SerialReturnError(messageId, Error_Illegal_Verb);
      }
    }
    if (strcmp(uri, "/main/devicename") == 0) {
      if (strcmp(verb, "GET") == 0) {
        MainDevicenameGet(messageId);
      }
      else {
        SerialReturnError(messageId, Error_Illegal_Verb);
      }
    }
    if (strcmp(uri, "/main/version") == 0) {
      if (strcmp(verb, "GET") == 0) {
        MainVersionGet(messageId);
      }
      else {
        SerialReturnError(messageId, Error_Illegal_Verb);
      }
    }
    if (strcmp(uri, "/main/enabled") == 0) {
      if (strcmp(verb, "GET") == 0) {
        MainEnabledGet(messageId);
      }
      else if (strcmp(verb, "PUT") == 0) {
        MainEnabledPut(messageId, root["args"]["enabled"]);
      }
      else {
        SerialReturnError(messageId, Error_Illegal_Verb);
      }
    }
    if (strcmp(uri, "/main/logging") == 0) {
      if (strcmp(verb, "PUT") == 0) {
        LoggingEnabled = root["args"]["enabled"];
        LoggingInterval = root["args"]["interval"];
        Serial.print("{\"messageId\":\"");
        Serial.print(messageId);
        Serial.println("\",\"result\":\"OK\"}");
      }
      else {
        SerialReturnError(messageId, Error_Illegal_Verb);
      }
    }
  }

  if (LoggingEnabled && (millis() - LastLogTime >= (100 * LoggingInterval))) { // measured in 1/10 sec
    LastLogTime = millis();
    SendStateMessage();
  }
}

void LowlevelEventsGet(char * messageId) {
  // send all of the event messages 
  sendEnabledChangeEvent();
  
  const size_t bufferSize = JSON_OBJECT_SIZE(2);
  DynamicJsonBuffer jsonBuffer(bufferSize);
  JsonObject& root = jsonBuffer.createObject();

  root["messageId"] = messageId;  
  root["events"] = "Echoed";
  root.printTo(Serial);
  Serial.println();
}

void MainDevicenameGet(char * messageId) {
  const size_t bufferSize = JSON_OBJECT_SIZE(2);
  DynamicJsonBuffer jsonBuffer(bufferSize);
  JsonObject& root = jsonBuffer.createObject();

  root["messageId"] = messageId;  
  if (strcmp(GetHardwareVersion(), Hardware_v0_4_VersionString) == 0)
    root["deviceName"] = "Holoseat Alpha";
  else
    root["deviceName"] = "Holoseat";
  root.printTo(Serial);
  Serial.println();
}

void MainVersionGet(char * messageId) {
  const size_t bufferSize = JSON_OBJECT_SIZE(4);
  DynamicJsonBuffer jsonBuffer(bufferSize);
  JsonObject& root = jsonBuffer.createObject();

  root["messageId"] = messageId; 
  root["hwVer"] = GetHardwareVersion();
  root["fwVer"] = FirmwareVersionString;
  root["hspVer"] = HspVersionString;
  root.printTo(Serial);
  Serial.println();
}

void MainEnabledGet(char* messageId) {
  const size_t bufferSize = JSON_OBJECT_SIZE(2);
  DynamicJsonBuffer jsonBuffer(bufferSize);
  JsonObject& root = jsonBuffer.createObject();

  root["messageId"] = messageId;  
  root["enabled"] = HoloseatEnabled;
  root.printTo(Serial);
  Serial.println();
}

void MainEnabledPut(char* messageId, int enabled) {
  if (HoloseatEnabled != enabled) {
    toggleEnabledState();
  }

  MainEnabledGet(messageId);
}

// set up enabled state variables
int enableReading = LOW;          
int enablePrevious = LOW;

// set up enable button elements
int enableLedPin = 13;
int enableButtonPin = 10;
Bounce debouncer = Bounce();

void setup() {
  // set up pins and debouncer library
  pinMode(enableLedPin, OUTPUT); //our ledPin is an output
  pinMode(enableButtonPin, INPUT_PULLUP); //we're reading from the button
  debouncer.attach(enableButtonPin);
  debouncer.interval(5); // interval in ms

  // configure DirectionPin for reading
  pinMode(DirectionPin, INPUT);

  Serial.begin(SerialBaudRate);    
  //MinTriggerPeriod = floor((1/TriggerStepsPerMax) * 60 * 1000);

  // start holoseat behavior
  InitializeWalkingVariables();
  EnableSensors(true);
  LastLogTime = millis();
  Keyboard.begin();
}

void toggleEnabledState() {
  HoloseatEnabled = !HoloseatEnabled;
  if (HoloseatEnabled) {
    digitalWrite(enableLedPin, HIGH);
  }
  else {
    digitalWrite(enableLedPin, LOW);
  }
  
  sendEnabledChangeEvent();
}

void sendEnabledChangeEvent() {
  const size_t bufferSize = JSON_OBJECT_SIZE(3);
  DynamicJsonBuffer jsonBuffer(bufferSize);

  JsonObject& root = jsonBuffer.createObject();
  root["messageId"] = "event";
  root["type"] = "enabledChange";
  root["enabled"] = HoloseatEnabled;

  root.printTo(Serial);
  Serial.println();
}

void loop() {
  // read from enable button
  debouncer.update();
  enableReading = debouncer.read();

  // read from serial port
  ProcessSerialData();
  
  // handle enable switching
  if (enableReading == HIGH && enablePrevious == LOW)
    toggleEnabledState();

  // handle "walking" (or not)
  if (HoloseatEnabled) {
    HandleWalking();
  }
  else {
    InitializeWalkingVariables();
  }
    
  // store previous enable reading for use in next iteration
  enablePrevious = enableReading;
}

// handle sensor data to determine walk state and act accordingly
void HandleWalking() {
  // disable interrupts while we do some math and work the keyboard
  EnableSensors(false);

  // calculate the Cadence
  unsigned long currentTime = millis();
  float localDeltaT = (currentTime - LastStepTime);  
  float deltaT = max(SensedDeltaT, localDeltaT)/1000; // in seconds
  Cadence = round(60.0/deltaT/NumPoles);  // in RPM

  // handle single stepping: single keypress for each cadence event while cadence
  // is below BaseTriggerCadence
  if (Cadence < BaseTriggerCadence) {
    if (StepTriggered) {  // if a step was triggered, do 1 step
      SelectKeyBasedOnDirection();
      PressDesiredKey();
      delay(100);  // approximate pressing and releasing the key
    }
  }

  // calculate CurrentTriggerCadence and handle general walking
  if (Cadence >= CurrentTriggerCadence) {   // only adjust trigger cadence when we pedal faster
    unsigned int cadenceLevel = Cadence / BaseTriggerCadence;  // e.g. 36 / 15 == 2
    unsigned int newTriggerCadence = cadenceLevel * BaseTriggerCadence;
    if (Cadence >= (newTriggerCadence + TriggerCadenceThreshold))
      CurrentTriggerCadence = newTriggerCadence;  // set new trigger cadence if we meet or exceed threshold

    // we know Cadence is fast enough, so select direction
    SelectKeyBasedOnDirection();
  }
  else {  // Cadence is not fast enough, will trigger
          // release of key for single step or general walking
    DesiredPressedKey = 0;
    CurrentTriggerCadence = BaseTriggerCadence;
    StepTriggered = false;
  }

  PressDesiredKey();
  
  // re-enbale the interrupts now that we are done
  EnableSensors(true);
}

void SelectKeyBasedOnDirection() {
  if (WalkingForward)
    DesiredPressedKey = WalkForwardCharacter;
  else
    DesiredPressedKey = WalkBackwardCharacter;
}

void PressDesiredKey() {
  // handle desired pressed key
  if (DesiredPressedKey != CurrentPressedKey) { // only need to do something when there is a change 
    if (!CurrentPressedKey) {
      // no key pressed so just press the desired key and record the pressed key
      Keyboard.press(DesiredPressedKey);
      CurrentPressedKey = DesiredPressedKey;
      }
    else if (!DesiredPressedKey) {
      // the desired key press is no keys
      Keyboard.release(CurrentPressedKey);
      CurrentPressedKey = DesiredPressedKey;
      }
    else {
      // the current key pressed is different than the key we desire: release, press, record 
      Keyboard.release(CurrentPressedKey);
      Keyboard.press(DesiredPressedKey);
      CurrentPressedKey = DesiredPressedKey;
      }
    }  
}

// resets walking state variables, used when holoseat is disabled
void InitializeWalkingVariables() {
  Keyboard.releaseAll();
  Cadence = 0.0;
  CurrentTriggerCadence = BaseTriggerCadence;
  StepTriggered = false;
  WalkingForward = true;
  SensedDeltaT = 5000;            // initialize sensed deltaT (and the value used to compute it, LastStepTime) to 5 seconds in the past
  LastStepTime = millis() - 5000; // as above
  CurrentPressedKey = 0;
  DesiredPressedKey = 0;
}
