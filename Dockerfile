FROM python:3.7-stretch

# https://github.com/wxWidgets/Phoenix/blob/master/README.rst#prerequisites
RUN apt-get -y update && apt-get -y install \
        dpkg-dev \
        build-essential \
        libjpeg-dev \
        libtiff-dev \
        libsdl1.2-dev \
        libgstreamer-plugins-base1.0-dev \
        libnotify-dev \
        freeglut3 \
        freeglut3-dev \
        libsm-dev \
        libgtk-3-dev \
        libwebkit2gtk-4.0-dev \
        libxtst-dev

RUN pip install pipenv

# https://wxpython.org/pages/downloads/
RUN pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/debian-9/wxPython-4.0.1-cp35-cp35m-linux_x86_64.whl wxPython

COPY . /app/
WORKDIR /app

RUN pipenv install --dev

