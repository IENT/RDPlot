#!/usr/bin/env python3

"""A setuptools based setup module.
"""

from setuptools import setup
from codecs import open
import platform
import os

here = os.path.abspath(os.path.dirname(__file__))

# GitPython is optional: use it if available, otherwise fall back to version.txt
try:
    import git  # type: ignore
except ImportError:
    git = None

# Get the long description from the README file
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

APP = ['src/rdplot/__main__.py']
OPTIONS = {
    'iconfile': 'src/rdplot/logo/PLOT1024.icns',
    'plist': {
        'CFBundleName': 'RDPlot',
        'CFBundleDisplayName': 'RDPlot',
        'CFBundleGetInfoString': "Making Sandwiches",
        'CFBundleIdentifier': "com.metachris.osx.sandwich",
        'CFBundleVersion': "0.1.0",
        'CFBundleShortVersionString': "0.1.0",
    },
}


def get_data_files_with_correct_location():
    """Set up the data_files variable correctly.
    If install happens on Linux:
        If install is done as root, system wide directories and files
        configured for it are used. Otherwise files are installed in users home directory.
    If install happens on Windows:
        no data_files necessary
    """
    data_files = []

    if 'Linux' in platform.system():
        if os.geteuid() == 0:
            # install as root or with sudo
            data_files = [
                ('/usr/share/pixmaps/', ['src/rdplot/logo/PLOT64.png']),
                ('/usr/share/applications/', ['src/rdplot/misc/rdplot.desktop']),
            ]
        elif 'FLATPAK_INSTALL' in os.environ:
            # install relative to prefix root
            # do nothing, will be handled by flatpak config
            pass
        else:
            # install as user
            data_files = [
                (
                    os.path.join(os.path.expanduser('~'), '.local/share/icons/'),
                    ['src/rdplot/logo/PLOT64.png'],
                ),
                (
                    os.path.join(os.path.expanduser('~'), '.local/share/applications/'),
                    ['src/rdplot/misc/rdplot.desktop'],
                ),
            ]

    return data_files


def _read_version_txt():
    """Read version string from version.txt in the project root, if present."""
    path = os.path.join(here, 'version.txt')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.readline().strip()
    except FileNotFoundError:
        return None


def get_version():
    """
    Determine version from git tags (if possible) or from version.txt.

    Git describe gives something like
        v1.0.0-158-g6c5be28
    We keep the first two numbers and replace the last with the number of commits since the tag:
        v1.0.0-158-g6c5be28 -> v1.0.158
    """
    if 'FLATPAK_INSTALL' in os.environ:
        git_describe = _read_version_txt()
        if not git_describe:
            raise RuntimeError("version.txt not found; cannot determine version.")
    else:
        git_describe = None

        if git is not None:
            # Try to get version from git
            try:
                repo = git.repo.Repo(here)
                git_describe = repo.git.describe('--tags').strip()

                # Write out version.txt for future installs (e.g. from an sdist)
                with open(os.path.join(here, 'version.txt'), 'w', encoding='utf-8') as f:
                    f.write(git_describe)

                # Also put it into the package itself
                pkg_version_path = os.path.join(here, 'src', 'rdplot', 'version.txt')
                with open(pkg_version_path, 'w', encoding='utf-8') as f:
                    f.write(git_describe)
            except Exception:
                # No git repository or git failed – fall back to version.txt
                git_describe = _read_version_txt()
        else:
            # GitPython not available – rely on version.txt
            git_describe = _read_version_txt()

        if not git_describe:
            raise RuntimeError(
                "Cannot determine version: neither GitPython+git metadata nor "
                "version.txt is available."
            )

    # Now parse git_describe into a version string
    split_describe = git_describe.split('-')

    if len(split_describe) == 1:
        # direct tag
        if '.' not in git_describe:
            raise Exception(
                "Tag does not comply to the versioning spec. "
                "It should be something like v1.0.0, but is %s" % git_describe
            )
        version = git_describe
    elif len(split_describe) == 3:
        # tag-commits-g<sha>
        tag = split_describe[0]
        commits_since_tag = split_describe[1]

        split_tag = tag.split('.')
        if len(split_tag) == 1:
            raise Exception(
                "Tag does not comply to the versioning spec. "
                "It should be something like v1.0.0, but is %s" % tag
            )

        # replace last digit with commits_since_tag
        split_tag[-1] = commits_since_tag
        version = '.'.join(split_tag)
    else:
        raise Exception(
            "Can not handle this type of git describe, there should be either "
            "no or two '-'. %s" % git_describe
        )

    return version


def get_install_requires():
    """Runtime dependencies (GitPython is intentionally NOT included)."""
    if 'FLATPAK_INSTALL' in os.environ:
        install_requires = [
            'cycler',
            'matplotlib',
            'numpy==1.26.4',
            'py',
            'pyparsing',
            'pyqt5',
            'pytest',
            'python-dateutil',
            'pytz',
            'six',
            'scipy',
            'tabulate',
            'mpldatacursor',
            'xmltodict',
            'jsonpickle',
            # 'tikzplotlib',
            'Pillow',
        ]
    else:
        install_requires = [
            'cycler',
            'matplotlib',
            'numpy',
            'py',
            'pyparsing',
            'pyqt5',
            'pytest',
            'python-dateutil',
            'pytz',
            'six',
            'scipy',
            'tabulate',
            'mpldatacursor',
            'xmltodict',
            'jsonpickle',
            # 'tikzplotlib',
            'Pillow',
        ]
    return install_requires


setup(
    app=APP,
    options={'py2app': OPTIONS},
    name='rdplot',

    version=get_version(),

    description='A plot tool for rate distortion curves',
    long_description=long_description,

    url='https://github.com/IENT/RDPlot',

    author='Jens Schneider, Johannes Sauer, Christoph Weyer, Alex Schmidt, Tim Claßen, Dominik Mehlem',
    author_email='classen@lfb.rwth-aachen.de',

    license='GPL-v3',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],

    keywords='video-coding bjontegaard-delta rate-distortion-plots',

    packages=['rdplot', 'rdplot.lib', 'rdplot.SimulationDataItemClasses', 'rdplot.Widgets'],
    package_dir={'': 'src'},

    include_package_data=True,

    install_requires=get_install_requires(),

    extras_require={},

    package_data={
        # paths are relative to the 'rdplot' package directory (src/rdplot)
        'rdplot': [
            'version.txt',
            'ui/*',
            'logo/*',
            'misc/*',
            'docs/about.html',
        ],
    },

    data_files=get_data_files_with_correct_location(),

    entry_points={
        'console_scripts': [
            'rdplot=rdplot.__main__:main',
        ],
    },
)