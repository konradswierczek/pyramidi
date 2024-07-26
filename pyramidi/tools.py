"""
"""
###############################################################################
# Standard Imports
import os
from time import time
###############################################################################
# Constants
__all__ = []
###############################################################################
def timer(func):
    """
    """
    def wrapper(
            *args,
            **kwargs
        ):
        """
        """
        start_time = time()
        result = func(
            *args,
            **kwargs
        )
        end_time = time()
        execution_time = end_time - start_time
        print(f"Elapsed Time: {execution_time:.2f}")
        return result
    return wrapper

###############################################################################
@timer
def parser(
    dir,
    extension = ".mid"
):
    """Accepts folder directory, returns root paths of all MIDI files."""
    data = []
    for root, dirs, files in os.walk(dir):
        for filename in files:
            nm, ext = os.path.splitext(filename)
            if ext.lower().endswith((extension)):
                data.append((root + "/" + filename))
    return data

##############################################################################