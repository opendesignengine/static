/*
 * Shepard Test Stand Experiment with Force Sensing Resistor (FSR)
 * Give a chart of the incoming voltage from the FSR and displays the value as a float.
 * Mach 30 Foundation for Space Development
 * www.mach30.org
 * 
 * Based on Oscilloscope, which is part of Accrochages
 * See http://accrochages.drone.ws
 * 
 * (c) 2008 Sofian Audry (info@sofianaudry.com)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */ 
 
 /*The serial port configuration is set up to work with Linux and not Windows*/
import processing.serial.*;

Serial port;  //The serial port we'll be communicating with
int val_front; //Data received from the serial port
int[] values_front; //The array that will hold the incoming values from the Arduino

/*Sets this app up for operation (window, serial, value storage, etc).*/
void setup() 
{
  //Set the size of the window
  size(640, 480);
  
  // Open the port that the board is connected to and use the same speed (9600 bps)
  //port = new Serial(this, "COM13", 115200); //FOR WINDOWS, CHANGE COM PORT FOR YOUR SYSTEM
  port = new Serial(this, "/dev/ttyACM0", 115200);
  
  //Initialize the array that holds the incoming data values
  values_front = new int[width];
  
  //Draw geometry with smooth edges
  smooth();
}

/*Scales the incoming values from the Arduino for display on the graph*/
int getY(int val) {
  //We've got 1024 values possible (0 - 1023), so scale that to the window's drawing area
  return (int)(val / 1023.0f * height) - 1;
}

/*The 0-1023 value that we get back corresponds to a voltage 0-5*/
float scaleVolts(int val) {
  return (float)((val / 1023.0f) * 5.0f);
}

/*Draws the value and chart to the screen*/
void draw()
{
  //As long as we're getting enough bytes to at least be the data identifier keep looping and reading
  while (port.available() >= 3) {
    //Get the incoming data identifier from the port
    int val= port.read();
    
    //Use the data identifier to separate the different types of sensor data coming back from the Arduino
    if (val == 0xff) {
      //Read the actual analog value from the Arduino    
       val_front = (port.read() << 8) | (port.read());           
    }   
  }
  
  //Loop through and store the incoming values
  for (int i = 0;i < width - 1;i++)
    values_front[i] = values_front[i+1];
    values_front[width-1] = val_front;
  
    //Background is black and lines/text are white
    background(0);
    stroke(255);
    
    //Step through the values and draw a corresponding line and text
    for (int x=1; x<width; x++) {
      //Draw the line
      line(width-x, height-1-getY(values_front[x-1]), width-1-x, height-1-getY(values_front[x]));  

      //Clear any text that has been there before
      fill(0);
      stroke(0);
      rect(10,10,150,20);
    
      //Display the current value as text
      fill(255);
      stroke(255);
      text("Voltage: " + scaleVolts(val_front),20,20);         
  }
}
