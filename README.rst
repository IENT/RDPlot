RDPlot
=======================

RDPlot is a tool for plotting rate distortion curves.
In particular, it can
- Parse the output of reference software such as HM, SHM, or VTM.
- Parse data points from xml-formatted files.
- Parse data from csv-formatted files.
- Calculate Bjontegaard Delta statistics.
- Export plots and BD statistics for camera ready presentation.

It was developed along the design principle of easy extensibility.
If no parse for your data is available, you can consider to introduce a `new parser <https://github.com/IENT/RDPlot/wiki/How-to-implement-a-new-parser>`_.
If you feel like your parser would be of interest for others, please submit a PR.

Build status
=======================
.. |Appveyor| image:: https://ci.appveyor.com/api/projects/status/y4gvft2pb3vmm4qe/branch/master?svg=true
  :target: https://ci.appveyor.com/project/JensAc/rdplot
.. |TravisCI| image:: https://travis-ci.org/IENT/RDPlot.svg?branch=master
  :target: https://travis-ci.org/IENT/RDPlot
.. |SnapCraft| image:: https://snapcraft.io/rdplot/badge.svg
  :target: https://snapcraft.io/rdplot

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

Installation via pipx
----
RDPlot is available on `PyPi <https://pypi.org/project/rdplot/>`_.
Therefore, you can directly install RDPlot via `pipx <https://pypi.org/project/pipx/>`_::

  pipx install rdplot

This should work on all platforms.
However, on Apple silicon you might have to fiddle a bit and use Rosetta.

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

Windows installer
----
For Windows an installer is available on the release page.
The installer will install a released version.
If you want to install the most recent (unreleased) version, you can download the installer from `Appveyors' artifacts <https://ci.appveyor.com/project/JensAc/rdplot/build/artifacts>`_.


Building from Source
=====================
We assume that you are familiar to Python development for the following sections.
If you run into any problems, don't hesitate to use the `Issue tracker <https://github.com/IENT/RDPlot/issues>`_.

.. contents::
   :local:

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

Mac OS X
--------
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

Uninstall is also simple: Just delete the local copy of the repositories and all aliases.

Running from repository without installation
=============================================
If you want to help improving RDPlot, you most probably need to run it directly from source for development and testing.

Linux
-----
You can start RDPlot from the command line with::

    PYTHONPATH=~PATH_TO_RDPLOT/src/ python3 PATH_TO_RDPLOT/src/rdplot/__main__.py

If you want to start the tool out of an IDE, make sure that you have set the PYTHONPATH environment variable correctly.
