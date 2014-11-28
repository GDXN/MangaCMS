
# This is just a note for how I built opencv with py3k support
# YMMV.

cmake -D CMAKE_BUILD_TYPE=RELEASE \
      -D BUILD_PYTHON_SUPPORT=ON \
      -D WITH_XINE=ON \
      -D WITH_OPENGL=ON \
      -D WITH_TBB=ON \
      -D BUILD_EXAMPLES=ON \
      -D BUILD_NEW_PYTHON_SUPPORT=ON \
      -D WITH_V4L=ON \
      -D PYTHON3_EXECUTABLE=/usr/bin/python3 \
      -D PYTHON_INCLUDE_DIR=/usr/include/python3.4 \
      -D PYTHON_INCLUDE_DIR2=/usr/include/x86_64-linux-gnu/python3.4m \
      -D PYTHON_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython3.4m.so \
      -D PYTHON3_NUMPY_INCLUDE_DIRS=/usr/local/lib/python3.4/dist-packages/numpy/core/include/ \
      ..