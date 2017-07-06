RDPlot
=======================

RdPlot is a tool for plotting rate distortion curves.  

Further information can be found in `src/rdplot/README.md
<https://git.rwth-aachen.de/IENT-Software/rd-plot-gui/blob/master/src/rdplot/README.md>`_.

Installation
========================

In the following sections different installation strategies are outlined:


On this level of the repository you can build a python package which is 
installable via pip3.

You can also build an app for OS X.

Linux 
=======================

The following was tested with Ubuntu 16.04. It should be similar for other
distributions.

First of all there is a conflict between the python3-matplotlib package for
Ubuntu and matplotlib installed from pip. 

RDPlot will only work with matplotlib
directly installed from pip and python3-matplotlib not installed on the system.

Make sure that you are using python 3 and pip is up to date.

Sadly but true, we need a few dependencies.  
You need to install them with::

    sudo apt-get install python3-jsonpickle python3-tk  python3-pip  python3-setuptools
    
and then::

    python setup.py sdist

Now you can install rdplot, either as user or system wide.
Install it system wide::

    sudo pip3 install --no-binary rdplot dist/rdplot-1.0.0.tar.gz

As user. This will install the binary to ~/.local/bin/rdplot. Make sure it is 
in your PATH. The desktop launcher also will work only if this is the case::

   pip3 install --user --no-binary rdplot  dist/rdplot-1.0.0.tar.gz

If you already have the tool installed run::

     sudo pip3 install --no-binary rdplot --upgrade dist/rdplot-1.0.0.tar.gz 
     
     
Now you should be able to run rdplot from the command line and have a
launcher in your favourite desktop enviroment.

If you do not want to build the distribution but a simple install run::
    
    sudo python setup.py install
    
Docker
=======================
If you prefer to run RDPlot in a Docker container, no problem::
    
    docker build rd-plot-gui/
    docker run -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix CONTAINERID
    
Make sure that you added your user to the docker group. If the container cannot connect to the display run::
    
    xhost local:docker
    
and try again. It should work.

**Note:** Most probably the dockerized version is something for enthusiasts. 
The image needs approx. 1.4 GB of disk-space. If you wanna spend that, enjoy!

Mac OS X
=======================

**Note:** things are not tested for Mac. You may have to fiddle a little bit.
Please contribute, if you have ideas for improvements.

First of all you need to install python3.
You can get it `here  
<https://www.python.org/downloads/>`_. 

Moreover, install all the requirements::
    
    cd src/rdplot
    pip3 install -r requirements.txt

Addtionally install py2app::
    
    pip3 install py2app

Then navigate back to the top level and build an app in alias mode::
    
    cd ../..
    python3 setup.py py2app -A
    
Now you should have an app in the dist folder.

**Note:** This app contains hard links to the directory with the source.
It is strongly recommended to clone the whole directory to your Applications folder.
Then you can simply build the app and launch it from the internal search.
Another possibility is to put an alias in your Applications folder and/or attach it to the Dock.

If you want to update the app, it is fairly easy:
Navigate to the local copy of the repository (now most probably in your Applications folder) and then::

    git pull
    python3 setup.py py2app -A
    
Done!

Unistall is also simple: Just delete the local copy of the repositories and all aliases.
    


Running from repository without installation
========================

Linux 
=======================

You can start rdplot from the command line with::
    PYTHONPATH=~PATH_TO_RDPLOT/src/ python PATH_TO_RDPLOT/src/rdplot/__main__.py

