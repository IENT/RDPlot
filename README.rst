RDPlot
=======================

RdPlot is a tool for plotting rate distortion curves.  

Further information can be found in src/rdplot/README.md

----

On this level of the repository you can build a python package which is 
installable via pip3.

----

Linux
=======================

First of all there is a conflict between the python3-matplotlib package for
Ubuntu and matplotlib installed from pip. 

RDPlot will only work with matplotlib
directly installed from pip and python3-matplotlib not installed on the system.

Make sure that you are using python 3 and pip is up to date and then::

    python setup.py sdist
     
    sudo pip3 install dist/rdplot-1.0.0.tar.gz 
    
If you already have the tool installed run::

     sudo pip3 install --upgrade dist/rdplot-1.0.0.tar.gz 
     
     
Now you should be able to run rdplot from the command line and have a
launcher in your favourite desktop enviroment.

if you do not build the distribution and simply install run::
    
    sudo python setup.py install
    
Docker
=======================
If you prefer to run RDPlot in a Docker container, no problem::
    
    docker build rd-plot-gui/
    docker run -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix CONTAINERID
    
Make sure that you added your user to the docker group. If the container cannot connect to the display run::
    
    xhost local:docker
    
and try again. It should work.





