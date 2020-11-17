import time
import os
import subprocess
import tempfile
#tempfile seems to have some weird interactions with imagemagick on my computer
#there are some solutions that I have found, but I am going to stick to using the
#cache directory listed in common.py
import imghdr
import struct

from autokey import common





class PatternNotFound(Exception):
    pass

def visgrep(image, detect, match: list, startx=0, starty=0, tolerance=0, logging=False):
    """
    Calls visgrep using C{subprocess}

    @param image: Path to image to search for a match
    @param detect: Path to image to try to find.
    @param match: List of images to try and find in image.
    @param startx: X coordinate of where to start scanning the image for detect.png (default 0)
    @param starty: Y coordinate of where to start scanning the image for detect.png (default 0)
    @param tolerance: Set tolerance for 'fuzzy' matches, higher numbers are more tolerant. (must be greater than 0)
    @param logging: Logs images used to ~/.config/autokey (whereever autokey settings are stored)
    @return: C{bool}, C{list of xy coordinates}
    """

    tol = int(tolerance)
    if tol < 0:
        raise ValueError("tolerance must be ≥ 0.")
    vg = subprocess.Popen(['visgrep', '-t', str(tol), '-X', startx, '-Y', starty, image, detect], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = vg.communicate()
    # at least one match was made
    coord_lines = out[0].decode().strip().split("\n")
    #each line will be "x,y i" where i is the "index" of each find
    #if the index is -1 it means
    if len(coord_lines)==0:
        return 0
    print(coord_lines)
    locations = []
    for line in coord_lines:
        xy = line.split(" ")[0].split(",")
        locations.append(xy)
    if locations[0][0]=='':
        return False, locations
    return True, locations

def visgrep_by_screen(detect, match: list=[], startx=0, starty=0, tolerance=0, logging=False):
    """
    Calls visgrep and passes it a screen shot of the entire screen.

    Returns in "C{boolean}, C{list} format, with the boolean being True if a match has been found, and the list
    being a list of the x,y coordinates of where they were found.

    @param detect: Path to image to try to find.
    @param match: List of images to try and find in image.
    @param startx: X coordinate of where to start scanning the image for detect.png (default 0)
    @param starty: Y coordinate of where to start scanning the image for detect.png (default 0)
    @param tolerance: Set tolerance for 'fuzzy' matches, higher numbers are more tolerant. (must be greater than 0)
    @param logging: Logs images used to ~/.config/autokey (whereever autokey settings are stored)
    @return: C{bool}, C{list of xy coordinates}
    """
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        subprocess.call(['import', '-window', 'root', f.name])
        if logging:
            __log_image_file(f.name, f.read())
        f.seek(0)
        return visgrep(f.name, detect, match, startx, starty, tolerance)

def visgrep_by_window_id(window_id, detect, match: list=[], startx=0, starty=0, tolerance=0, logging=False):
    """
    Calls C{visgrep} and passes it a window id (from wmctrl). Uses C{import} to take a screen shot of the window, as it appears
    on the screen (with other windows overlapping) minus the topbar from whatever window manager is being used.

    Uses wmctrl -lG to obtain window geometry using the window_id, using this and import we can accurately return values for where things appear while
    greatly increasing speed by decreasing the size visgrep has to search for the matches.
    
    """
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        subprocess.call(['import', '-screen', '-window', window_id, f.name])
        if logging:
            __log_image_file(f.name, f.read())
        f.seek(0)
        #should return relative or absolute?
        #absolute
        return visgrep(f.name, detect, match, startx, starty, tolerance)

def visgrep_by_window_title(title, detect, match: list=[], startx=0, starty=0, tolerance=0, logging=False):
    l = window.get_window_list(title)
    if len(l)==0: #no matches were found by get_window_list
        return False, []
    else: #go with the first match?
        return visgrep_by_window_id(l[0][0], detect, match, startx, starty, tolerance, logging)


def __log_image_file(filename, read):
    """
    Function to make a copy of the screenshots take by visgrep in the autokey CONFIG_DIR.
    """
    with open(common.CONFIG_DIR+"/"+filename.split("/")[-1], "wb+") as log:
        log.write(read)