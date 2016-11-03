This project implements a GUI for displaying rd-plots of encoded video sequences.

Functionalties (which will be developed)
- Display rd plots
- Select component to be plotted (YUV, Y,U,V)
- Add multiple plot widgets, change between them
- Open single encoder logs
- Open whole directories, parsing all found plots
- A GUI for importing logs, which scan the filesystem under a selected directory
- Plot rd plot over time (rate over time, psnr over time, or 3d rd-time)
- Exporting plots (through matplotlib interface)
- Display table of rd results
- export tables as latex style table code
- simulation folder comparison mode: select different directories. list only displays the directories. selector to choose which sequence to look at


Installation using virtual env and pycharm (not working yet, problem with pyqt4)
- Open the project folder in pycharm
-> File -> Settings -> Project: rd-plot-gui -> Project Interpreter -> Settings symbol -> Create VirtualEnv (Use python 3.x as base interpreter)
-> open terminal -> cd project folder -> source ~/path-to-the-virtual-env/bin/activate
-> pip install --upgrade pip
-> pip install -r requirements.txt

Now you should be able to run the project from the virtual env
