#!/usr/bin/env python3

"""A setuptools based setup module.
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
import platform
import os
import git 

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

APP = ['src/rdplot/__main__.py']
OPTIONS = {'iconfile': 'src/rdplot/logo/PLOT1024.icns',
           'plist': {
               'CFBundleName': 'RDPlot',
               'CFBundleDisplayName': 'RDPlot',
               'CFBundleGetInfoString': "Making Sandwiches",
               'CFBundleIdentifier': "com.metachris.osx.sandwich",
               'CFBundleVersion': "0.1.0",
               'CFBundleShortVersionString': "0.1.0"}
           }


def get_data_files_with_correct_location():
    """Set up the data_files variable correctly.
    If install happens on Linux:
        If install is done as root, system wide directories and files
        configured for it are used. Otherwise files are installed in users home directory.
    If install happens on Windows:
        no data_files necessary"""
    data_files = []

    if 'Linux' in platform.system():
        if os.geteuid() != 0:
            # install as user
            data_files = [
                (os.path.join(os.path.expanduser('~'), '.local/share/icons/'), ['src/rdplot/logo/PLOT64.png']),
                (os.path.join(os.path.expanduser('~'), '.local/share/applications/'),
                 ['src/rdplot/misc/rdplot.desktop'])]


        else:
            # install as root or with sudo
            data_files = [('/usr/share/pixmaps/', ['src/rdplot/logo/PLOT64.png']),
                          ('/usr/share/applications/', ['src/rdplot/misc/rdplot.desktop'])]

    return data_files


def get_version():
    """
    Read git tag and version given by environment variable and convert it to a version number.
    Git describe gives something like
        v1.0.0-158-g6c5be28
    From the git describe help:
        The command finds the most recent tag that is reachable from a commit.
        If the tag points to the commit, then only the tag is shown. Otherwise,
        it suffixes the tag name with the number of additional commits on top
        of the tagged object and the abbreviated object name of the most recent
        commit.
    We will keep the first two number and replace the last with the number of commits since the tag:
        v1.0.0-158-g6c5be28 -> v1.0.158
    :return:
    """

    r = git.repo.Repo('../')
    git_describe = r.git.describe()
    version = None
    split_describe = git_describe.split('-')
    if len(split_describe) == 1:
        if '.' not in git_describe:
            raise Exception("Tag does not comply to the versioning spec. It should be something like v1.0.0, but is %s"
                            % git_describe)
        version = git_describe
    elif len(split_describe) == 3:
        tag = split_describe[0]
        commits_since_tag = split_describe[1]

        # replace last digit with commits_since_tag
        split_tag = tag.split('.')
        if len(split_tag) == 1:
            raise Exception("Tag does not comply to the versioning spec. It should be something like v1.0.0, but is %s"
                            % tag)
        split_tag[-1] = commits_since_tag
        version = '.'.join(split_tag)

    else:
        raise Exception("Can not handle this type of git describe, there should be either no or two '-'. %s"
                        % git_describe)

    return version


setup(
    app=APP,
    options={'py2app': OPTIONS},
    name='rdplot',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=get_version(),

    description='A plot tool for rate distortion curves',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/IENT/RDPlot',

    # Author details
    author='Jens Schneider, Johannes Sauer, Christoph Weyer, Alex Schmidt',
    author_email='schneider@ient.rwth-aachen.de',

    # Choose your license
    license='GPL-v3',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Information Analysis',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

    ],

    # What does your project relate to?
    keywords='video-coding bjontegaard-delta rate-distortion-plots',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=['rdplot', 'rdplot.lib', 'rdplot.SimulationDataItemClasses', 'rdplot.Widgets'],
    package_dir={'': 'src'},

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    # py_modules=["my_module"],
    include_package_data=True,

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['cycler', 'matplotlib', 'numpy', 'py', 'pyparsing', 'pyqt5<5.11', 'pytest', 'python-dateutil', 'pytz',
                      'sip', 'six', 'scipy', 'tabulate', 'mpldatacursor',
                      'xmltodict', 'jsonpickle'],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={},

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'rdplot': ['src/rdplot/ui/*', 'src/rdplot/logo/*', 'src/rdplot/misc/*', 'src/rdplot/docs/about.html'],
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=get_data_files_with_correct_location(),

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'rdplot=rdplot.__main__:main',
        ],
    },
)
