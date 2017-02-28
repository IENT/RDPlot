FROM ubuntu:latest

RUN useradd -ms /bin/bash rdplotuser

# install stuff
RUN apt-get -y update && \
    apt-get -y install python3 && \
    apt-get -y install python3-pip && \
    apt-get -y install python3-pyqt5 && \
    apt-get -y install python3-tk && \
    pip3 install --upgrade pip

# Install app dependencies
COPY . /rdplot/

RUN cd /rdplot/ && \
    python3 setup.py sdist && \
    pip3 install dist/rdplot-1.0.0.tar.gz 

USER rdplotuser

CMD ["rdplot"]

