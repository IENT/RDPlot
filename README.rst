RDPlot 
=======================

RdPlot is a tool for plotting rate distortion curves.  

Further information can be found in `src/rdplot/README.md
<https://github.com/IENT/RDPlot/blob/master/src/rdplot/README.md>`_.

Build status
=======================
.. |Appveyor| image:: https://ci.appveyor.com/api/projects/status/y4gvft2pb3vmm4qe/branch/master?svg=true
  :target: https://ci.appveyor.com/project/JensAc/rdplot
.. |TravisCI| image:: https://travis-ci.org/IENT/RDPlot.svg?branch=master
  :target: https://travis-ci.org/IENT/RDPlot 
.. |SnapCraft| image:: https://build.snapcraft.io/badge/IENT/RDPlot.svg
  :target: https://build.snapcraft.io/user/IENT/RDPlot
  
+------------+------------+-------------+
|  AppVeyor  | Travis CI  |  SnapCraft  |
+============+============+=============+
| |Appveyor| | |TravisCI| | |SnapCraft| |
+------------+------------+-------------+

Code Coverage
=======================
.. image:: https://coveralls.io/repos/github/IENT/RDPlot/badge.svg?branch=master
  :target: https://coveralls.io/github/IENT/RDPlot

Installation
========================

.. contents::
   :local:

In the following sections different installation strategies are outlined:

On this level of the repository you can build a python package which is 
installable via pip3.

You can also build an app for OS X.

For Windows an installer is available on the release page.

Linux 
-----

Snap
_____

You can install RDPlot directly via snap for various Linux distributions. 
It was tested with Ubuntu 16.04 and Arch Linux. 
Be aware of the fact that you cannot access any directory in your system when rdplot is installed via snap. 
This is due to the confinement limitations of snaps.
You will have access to /home and /media.
Therefore, you should make sure, that the data you want to plot is accessible under these directories. 
If you feel comfortable with that::

    sudo snap install rdplot
    sudo snap connect rdplot:removable-media

Note, that connecting removable-media is not necessary, if you do not wish to acess files 
under /media.

Building from Source 
____________________

The following was tested with Ubuntu 16.04. It should be similar for other
distributions.

First of all there is a conflict between the python3-matplotlib package for
Ubuntu and matplotlib installed from pip. 

RDPlot will only work with matplotlib
directly installed from pip and python3-matplotlib not installed via the system packet manager (e.g. apt).
If you need system packages that conflict with the packages required for RDPlot, you can use a python virtual environment (see below).
The general recommendation for installing python packages is to use pip.

Make sure that you are using python 3 and pip is up to date::

    python3 -V
    pip3 -V
    sudo pip3 install --upgrade pip
    
Note: python2 has been retired_ in 2020. python3 might also be called simply python on your system.

.. _retired: https://www.python.org/doc/sunset-python-2/
    
If missing, install python3::

    sudo apt-get install python3
    
If missing, install pip3::

    sudo sh -c "curl https://bootstrap.pypa.io/get-pip.py | python3"

Sadly but true, we need a few dependencies.  
You need to install them with either your system packet manager, **or** pip::

    sudo apt-get install python3-jsonpickle python3-setuptools python3-git # <- apt OR
    sudo pip3 install gitpython                                            # <- pip
    
Now we can download the source and build our rdplot package::

    git clone --depth 1 https://github.com/IENT/RDPlot && cd RDPlot # alternativly download and unpack current stable from  https://github.com/IENT/RDPlot/releases
    python3 setup.py sdist

Now you can install rdplot, either as user or system wide.
Install it system wide::

    sudo pip3 install --no-binary rdplot dist/rdplot-*.tar.gz

As user. This will install the binary to ~/.local/bin/rdplot. Make sure it is 
in your PATH. The desktop launcher also will work only if this is the case::

    pip3 install --user --no-binary rdplot  dist/rdplot-*.tar.gz

If you already have the tool installed run::

    sudo pip3 install --no-binary rdplot --upgrade dist/rdplot-*.tar.gz 
     
     
Now you should be able to run rdplot from the command line and have a
launcher in your favourite desktop enviroment.

If you do not want to build the distribution but a simple install run::
    
    sudo python setup.py install

Virtual Environment
___________________
If you need system packages that conflict with the packages required for RDPlot, you can use a python virtual environment (see below).

When you are inside a virtual environment, python ignores all system packages and instead uses a dedicated environment, allowing you to install packages with pip that would otherwise conflict with system packages and/or different versions. The pitfall is that you need to activate the environment each time you want to use the program.

You can find more info on virtual environments at https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/.

venv is included in python since version 3.3. If your python version is older consider upgrading, or install venv using::

    sudo pip install virtualenv
    
Download RDPlot. Make sure you do this at a place where it can stay::

    git clone --depth 1 https://github.com/IENT/RDPlot
    cd RDPlot
    
Create a virtualenv named "env" inside the RDPlot directory::

    python3 -m venv env
    
Activate the venv and install dependencies::
    
    source env/bin/activate
    pip3 install --upgrade pip gitpython
    
Build and install RDPlot::

    python3 setup.py sdist
    pip3 install --no-binary rdplot --upgrade dist/rdplot-*.tar.gz
    
Leave the environment::

    deactivate
    
Remember to activate the environment every time you want to run RDPlot::

    cd RDPlot
    source env/bin/activate
    rdplot
    deactivate

To uninstall, simply delete the RDPlot directory.
    
Windows
-------
As mentioned above you can find an installer on the release page. Download, install, done.

Docker
------
If you prefer to run RDPlot in a Docker container, no problem::
    
    docker build rd-plot-gui/
    docker run -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix CONTAINERID
    
Make sure that you added your user to the docker group. If the container cannot connect to the display run::
    
    xhost local:docker
    
and try again. It should work.

**Note:** Most probably the dockerized version is something for enthusiasts. 
It is not really tested and the image needs approx. 1.4 GB of disk-space. 
If you want to spend that, enjoy!

Mac OS X
-----
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
=============================================

Linux 
-----

You can start rdplot from the command line with::

    PYTHONPATH=~PATH_TO_RDPLOT/src/ python3 PATH_TO_RDPLOT/src/rdplot/__main__.py
    
If you want to start the tool out of an IDE like PyCharm, make sure that you have set the PYTHONPATH environment variable correctly.
