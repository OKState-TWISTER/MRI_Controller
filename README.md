# MRI_Controller
Software to automate measurements and control the MRI carts.

# How to Use the 2D Sweep Measurement System

This guide explains how to set up and use the **2D Sweep Measurement System**. The system will move a device across a 2D grid (azimuth and elevation) and take measurements at each position using a scope. The results will be saved in a MATLAB-compatible `.mat` file for further analysis.

## Prerequisites

Before using the system, ensure the following:

1. **Hardware Setup**:
Stepper Motor Azimuth (PUL) - GPIO 22   
Stepper Motor Azimuth (DIR) - GPIO 27       
Stepper Motor Azimuth (ENA) - GPIO 17  
Stepper Motor Elevation (PUL) - GPIO 23   
Stepper Motor Elevation (DIR) - GPIO 24     
Stepper Motor Elevation (ENA) - GPIO 25   

2. **Software Setup**:
    - Install Python 3 and necessary libraries. The following libraries are used in the code:
      - `socket`: For network communication.
      - `keyboard`: To detect key input without pressing enter.
      - `time`: For timing-related operations.
      - `configparser`: For reading and writing configuration files.
      - `numpy`: For numerical operations.
      - `sys`: For system-specific parameters and functions.
      - `twister_api.oscilloscope_interface`: For communication with the oscilloscope.
      - `twister_api.twister_utils`: Utility functions for the Twister API.
      - `twister_api.fileio`: File input/output operations.
      - `scipy`: For scientific computing (e.g., saving data in MATLAB format).
      - `os`: For file and directory operations.
      - `datetime`: To get and format the current date.

    To install dependencies, use the following commands:
    ```bash
    pip install numpy scipy keyboard twister_api
    ```


## Usage

Follow these steps to run the 2D sweep:

### 1. **Prepare the Parameters**

You will need to define the following parameters:

- **Start and End Azimuth**: The range of azimuth angles you want to sweep across.
- **Start and End Elevation**: The range of elevation angles you want to sweep across.
- **Step Size**: The step size for both azimuth and elevation (i.e., how much to move the device between measurements).
- **Save Folder**: The folder where the measurement data will be saved.

Use the existing config.ini file to do this on the PC and save it when inputs have been entered. The save folder is defined in the header of UTOL_Motion_Control_pc.py

### 2. **Start the Pi Server**
On the pi, start the UTOL_Motion_Control_pi.py script and ensure it prints out that it is listening on a port.

### 3. **Run the PC Controller Code**
On the pc, start the UTOL_Motion_Control_pc.py code. You may have to run this as admin and enter your password due to the keyboard input code. The code will run as follows:
1. When first run, the code will enter a setup mode that allows the user to select a start location controlling the motor stage with the keyboard. When you are satisfied with this, press 'q' to quit and begin the sweep.
2. The sweep will start by moving to the bottom left corner of the sweep and doing a serpentine approach to the top, taking measurements at each point. It also will record the current position of the azimuth and elevation in the config file in case of an interruption. At any point, the 'q' key can be pressed to pause the measurement and pressed again to start. 
3. When completed with the sweep, the code will exit the sweep and save the results to the given filepath.
