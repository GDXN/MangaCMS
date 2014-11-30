
# This is just a note for how I built opencv with py3k support
# YMMV.

# also needs the following ubuntu packages
 - libtbb-dev
 - libxine2-dev
 - libopenexr-dev
 - libgtk2.0-dev
 - libv4l-dev
 - libavformat-dev
 - libgstreamer0.10-dev
 - libgstreamer-plugins-base1.0-dev
 - libswscale-dev
 - libtiff4-dev

sudo apt-get install              \
            build-essential       \
            libgtk2.0-dev         \
            libjpeg-dev           \
            libtiff4-dev          \
            libjasper-dev         \
            libopenexr-dev        \
            cmake                 \
            libtbb-dev            \
            libeigen3-dev         \
            yasm libfaac-dev      \
            libopencore-amrnb-dev \
            libopencore-amrwb-dev \
            libtheora-dev         \
            libvorbis-dev         \
            libxvidcore-dev       \
            libx264-dev           \
            libdc1394-22-dev      \
            libavcodec-dev        \
            libavformat-dev       \
            libswscale-dev

xfeatures2d

# Note: requires the opencv_contrib AND the opencv_extra repos as well, for SIFT functions.

#
# This is assuming that all three repos (opencv, opencv_contrib and the opencv_extra) are cloned
# into your ~/ directory. The cmake command is run from ~/opencv/build (you have to create the 'build' dir)
# Getting the SIFT functions to work is kind of a giant PITA.

cmake -D CMAKE_BUILD_TYPE=RELEASE                                                              \
      -D BUILD_PYTHON_SUPPORT=ON                                                               \
      -D WITH_XINE=ON                                                                          \
      -D WITH_OPENGL=ON                                                                        \
      -D WITH_TBB=ON                                                                           \
      -D BUILD_EXAMPLES=ON                                                                     \
      -D BUILD_NEW_PYTHON_SUPPORT=ON                                                           \
      -D PYTHON_EXECUTABLE=/usr/bin/python3                                                    \
      -D INSTALL_C_EXAMPLES=ON                                                                 \
      -D INSTALL_PYTHON_EXAMPLES=ON                                                            \
      -D PYTHON_INCLUDE_DIR=/usr/include/python3.4                                             \
      -D PYTHON_INCLUDE_DIR2=/usr/include/x86_64-linux-gnu/python3.4m                          \
      -D PYTHON_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython3.4m.so                             \
      -D PYTHON_NUMPY_INCLUDE_DIRS=/usr/local/lib/python3.4/dist-packages/numpy/core/include/  \
      -D PYTHON_PACKAGES_PATH=/usr/local/lib/python3.4/dist-packages/numpy/core/include/       \
      -D BUILD_OPENCV_JAVA=NO                                                                  \
      -D OPENCV_EXTRA_MODULES_PATH=~/b_opencv/opencv_contrib/modules                           \
      -D OPENCV_TEST_DATA_PATH=~/b_opencv/opencv_extra/testdata                                \
      -D PYTHON3_EXECUTABLE=/usr/bin/python3                                                   \
      -D PYTHON3_NUMPY_INCLUDE_DIRS=/usr/local/lib/python3.4/dist-packages/numpy/core/include/ \
      ..



mkdir build
cd build
cmake -D WITH_TBB=ON
      -D BUILD_NEW_PYTHON_SUPPORT=ON
      -D WITH_V4L=ON
      -D BUILD_EXAMPLES=ON

      -D WITH_VTK=ON .
      -D WITH_OPENGL=ON




