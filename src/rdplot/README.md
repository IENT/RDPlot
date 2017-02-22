# RD Plot
![RD Plot logo](https://git.rwth-aachen.de/IENT-Software/rd-plot-gui/raw/master/src/rdplot/logo/PLOT256.png)  

# Functionalties
RD Plot is a plotting tool for visualizing rate-distortion data parsed from  
encoder log files of common video coding reference software packages.  
It can:
- Display rate-distortion plots
- Select component to be plotted (YUV, Y, U, V and even more)
- Plot rd plot over time (rate over time, psnr over time)
- Exporting plots (through matplotlib interface)
- Calculate and display table of bjontegaard delta measurement
- Export tables as latex style table code


# Installation 
## in a virtual enviroment using pycharm 
- Open the project folder in pycharm
- -> File -> Settings -> Project: rd-plot-gui -> Project Interpreter -> Settings symbol -> Create VirtualEnv (Use python 3.x as base interpreter)
- -> open terminal -> cd project folder -> source ~/path-to-the-virtual-env/bin/activate
- -> pip install --upgrade pip
- -> pip install -r requirements.txt

Now you should be able to run the project from the virtual env

## on Ubuntu
    sudo apt get python3-pyqt5 python3-matplotlib python3-pip python3-scipy
    pip3 install mpldatacursor
Now you are able to call __init__.py from the command line


# Scripts
Helper script to start the gui and load all files and folders from the
*example_simulation_data*. Invoke the script with
``` python -m script.start_gui_and_parse_simulation_examples ```
from the project main folder ie. the folder, which contains this file.
