int sensorPin_front = A0; // A0 is the input pin for front fsr
//int sensorPin_back = A1; // A1 is the input pin for back fsr

int sensorValue_front = 0; // variable to store the value coming from the sensor
//int sensorValue_back = 0;

int ledPin = 13; //The LED pin is used in serial comms

void setup() {
// initialize serial:
Serial.begin(115200);
// declare the ledPin as an OUTPUT:
pinMode(ledPin, OUTPUT);
}

void loop() {
// read the value from the sensor:
sensorValue_front = analogRead(sensorPin_front);
//sensorValue_back = analogRead(sensorPin_back);

//send over serial
Serial.write( 0xff); //control byte
Serial.write( (sensorValue_front >> 8) & 0xff); //first byte
Serial.write( sensorValue_front & 0xff); //second byte
//Serial.write( 0xfe);
//Serial.write( (sensorValue_back >> 8) & 0xff);
//Serial.write( sensorValue_back & 0xff);
//delay(100);
}
