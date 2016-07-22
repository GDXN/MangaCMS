
# Yeah. just used for ~~one~~ two boolean flags.
run = True

# Determines if proxies in nameTools preload contents when started.
preloadDicts = False

import multiprocessing
run_state     = multiprocessing.Value('i', 1)

notq = None