
# This is just a note for how I built opencv with py3k support
# YMMV.

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
      -D PYTHON3_EXECUTABLE=/usr/bin/python3                                                   \
      -D PYTHON_INCLUDE_DIR=/usr/include/python3.4                                             \
      -D PYTHON_INCLUDE_DIR2=/usr/include/x86_64-linux-gnu/python3.4m                          \
      -D PYTHON_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython3.4m.so                             \
      -D PYTHON3_NUMPY_INCLUDE_DIRS=/usr/local/lib/python3.4/dist-packages/numpy/core/include/ \
      -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules                                    \
      -D OPENCV_TEST_DATA_PATH=~/opencv_extra/testdata                                         \
      ..