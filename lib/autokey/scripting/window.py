# Copyright (C) 2011 Chris Dekter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Basic window management. Requies C{wmctrl} to be installed."""

import re
import subprocess
import time


class Window:
    """
    Basic window management using wmctrl

    Note: in all cases where a window title is required (with the exception of wait_for_focus()),
    two special values of window title are permitted:

    :ACTIVE: - select the currently active window
    :SELECT: - select the desired window by clicking on it
    """

    def __init__(self, mediator):
        self.mediator = mediator

    def wait_for_focus(self, title, timeOut=5):
        """
        Wait for window with the given title to have focus

        Usage: C{window.wait_for_focus(title, timeOut=5)}

        If the window becomes active, returns True. Otherwise, returns False if
        the window has not become active by the time the timeout has elapsed.

        @param title: title to match against (as a regular expression)
        @param timeOut: period (seconds) to wait before giving up
        @rtype: boolean
        """
        regex = re.compile(title)
        waited = 0
        while waited <= timeOut:
            if regex.match(self.mediator.interface.get_window_title()):
                return True

            if timeOut == 0:
                break  # zero length timeout, if not matched go straight to end

            time.sleep(0.3)
            waited += 0.3

        return False

    def wait_for_exist(self, title, timeOut=5):
        """
        Wait for window with the given title to be created

        Usage: C{window.wait_for_exist(title, timeOut=5)}

        If the window is in existence, returns True. Otherwise, returns False if
        the window has not been created by the time the timeout has elapsed.

        @param title: title to match against (as a regular expression)
        @param timeOut: period (seconds) to wait before giving up
        @rtype: boolean
        """
        regex = re.compile(title)
        waited = 0
        while waited <= timeOut:
            retCode, output = self._run_wmctrl(["-l"])
            for line in output.split('\n'):
                if regex.match(line[14:].split(' ', 1)[-1]):
                    return True

            if timeOut == 0:
                break  # zero length timeout, if not matched go straight to end

            time.sleep(0.3)
            waited += 0.3

        return False

    def activate(self, title, switchDesktop=False, matchClass=False):
        """
        Activate the specified window, giving it input focus

        Usage: C{window.activate(title, switchDesktop=False, matchClass=False)}

        If switchDesktop is False (default), the window will be moved to the current desktop
        and activated. Otherwise, switch to the window's current desktop and activate it there.

        @param title: window title to match against (as case-insensitive substring match)
        @param switchDesktop: whether or not to switch to the window's current desktop
        @param matchClass: if True, match on the window class instead of the title
        """
        if switchDesktop:
            args = ["-a", title]
        else:
            args = ["-R", title]
        if matchClass:
            args += ["-x"]
        self._run_wmctrl(args)

    def close(self, title, matchClass=False):
        """
        Close the specified window gracefully

        Usage: C{window.close(title, matchClass=False)}

        @param title: window title to match against (as case-insensitive substring match)
        @param matchClass: if True, match on the window class instead of the title
        """
        if matchClass:
            self._run_wmctrl(["-c", title, "-x"])
        else:
            self._run_wmctrl(["-c", title])

    def resize_move(self, title, xOrigin=-1, yOrigin=-1, width=-1, height=-1, matchClass=False):
        """
        Resize and/or move the specified window

        Usage: C{window.close(title, xOrigin=-1, yOrigin=-1, width=-1, height=-1, matchClass=False)}

        Leaving and of the position/dimension values as the default (-1) will cause that
        value to be left unmodified.

        @param title: window title to match against (as case-insensitive substring match)
        @param xOrigin: new x origin of the window (upper left corner)
        @param yOrigin: new y origin of the window (upper left corner)
        @param width: new width of the window
        @param height: new height of the window
        @param matchClass: if True, match on the window class instead of the title
        """
        mvArgs = ["0", str(xOrigin), str(yOrigin), str(width), str(height)]
        if matchClass:
            xArgs = ["-x"]
        else:
            xArgs = []
        self._run_wmctrl(["-r", title, "-e", ','.join(mvArgs)] + xArgs)

    def move_to_desktop(self, title, deskNum, matchClass=False):
        """
        Move the specified window to the given desktop

        Usage: C{window.move_to_desktop(title, deskNum, matchClass=False)}

        @param title: window title to match against (as case-insensitive substring match)
        @param deskNum: desktop to move the window to (note: zero based)
        @param matchClass: if True, match on the window class instead of the title
        """
        if matchClass:
            xArgs = ["-x"]
        else:
            xArgs = []
        self._run_wmctrl(["-r", title, "-t", str(deskNum)] + xArgs)

    def switch_desktop(self, deskNum):
        """
        Switch to the specified desktop

        Usage: C{window.switch_desktop(deskNum)}

        @param deskNum: desktop to switch to (note: zero based)
        """
        self._run_wmctrl(["-s", str(deskNum)])

    def set_property(self, title, action, prop, matchClass=False):
        """
        Set a property on the given window using the specified action

        Usage: C{window.set_property(title, action, prop, matchClass=False)}

        Allowable actions: C{add, remove, toggle}
        Allowable properties: C{modal, sticky, maximized_vert, maximized_horz, shaded, skip_taskbar,
        skip_pager, hidden, fullscreen, above}

        @param title: window title to match against (as case-insensitive substring match)
        @param action: one of the actions listed above
        @param prop: one of the properties listed above
        @param matchClass: if True, match on the window class instead of the title
        """
        if matchClass:
            xArgs = ["-x"]
        else:
            xArgs = []
        self._run_wmctrl(["-r", title, "-b" + action + ',' + prop] + xArgs)

    def get_active_geometry(self):
        """
        Get the geometry of the currently active window

        Usage: C{window.get_active_geometry()}

        @return: a 4-tuple containing the x-origin, y-origin, width and height of the window (in pixels)
        @rtype: C{tuple(int, int, int, int)}
        """
        active = self.mediator.interface.get_window_title()
        result, output = self._run_wmctrl(["-l", "-G"])
        matchingLine = None
        for line in output.split('\n'):
            if active in line[34:].split(' ', 1)[-1]:
                matchingLine = line

        if matchingLine is not None:
            output = matchingLine.split()[2:6]
            # return [int(x) for x in output]
            return list(map(int, output))
        else:
            return None

    def get_active_title(self):
        """
        Get the visible title of the currently active window

        Usage: C{window.get_active_title()}

        @return: the visible title of the currentle active window
        @rtype: C{str}
        """
        return self.mediator.interface.get_window_title()

    def get_active_class(self):
        """
        Get the class of the currently active window

        Usage: C{window.get_active_class()}

        @return: the class of the currentle active window
        @rtype: C{str}
        """
        return self.mediator.interface.get_window_class()

    def center_window(self, title=":ACTIVE:", win_width=None, win_height=None, monitor=0, matchClass=False):
        """
        Centers the active (or window selected by title) window. Requires xrandr for getting monitor sizes and offsets.

        @param title: Title of the window to center (defaults to using the active window)
        @param win_width: Width of the centered window, defaults to screenx/3. Use -1 to center without size change.
        @param win_height: Height of the centered window, defaults to screeny/3. Use -1 to center without size change.
        @param monitor: Monitor number (0 is primary, listed via C{xrandr --listactivemonitors} etc.)
        @param matchClass: if True, match on the window class instead of the title
        @raises ValueError: If title or desktop is not found by wmctrl
        """
        #could also use Gdk.Display.get_default().get_montiors etc.
        #Used xrandr for ease of cross Gtk/Qt use
        #Example Output:
        #Monitors: 2
        # 0: +*HDMI-0 1920/521x1080/293+0+0  HDMI-0
        # 1: +DVI-D-0 1440/408x900/255+1920+0  DVI-D-0
        # Regex gets  ____ and ____    ____ _
        # this translates to monitor x and y size, and x and y offset for each monitor
        returncode, output = self._run_xrandr(["--listactivemonitors"])
        regex = r" (\d{3,4}).*?x(\d{3,4})\/.*?\+(\d{1,4})\+(\d{1,4})"
        matches = re.findall(regex, output, re.MULTILINE)
        x_offset = int(matches[monitor][2])
        y_offset = int(matches[monitor][3])
        width = int(matches[monitor][0])
        height = int(matches[monitor][1])
        #work backwards from the size of the window
        if win_width is None:
            win_width = round(width/2)
        if win_height is None:
            win_height = round(height/2)
        top_x = round((width-win_width)/2)
        top_y = round((height-win_height)/2)

        #remove maximized attributes from window
        self.set_property(title, "remove", "maximized_vert", matchClass=matchClass)
        self.set_property(title, "remove", "maximized_horz", matchClass=matchClass)
        #resize and move window
        self.resize_move(title, x_offset+top_x, y_offset+top_y, win_width, win_height, matchClass=matchClass)

    def _run_xrandr(self, args):
        try:
            with subprocess.Popen(["xrandr"] + args, stdout=subprocess.PIPE) as p:
                output = p.communicate()[0].decode()[:-1]
                returncode = p.returncode
        except FileNotFoundError:
            return 1, "ERROR: Please install xrandr"

        return returncode, output

    def _run_wmctrl(self, args):
        try:
            with subprocess.Popen(["wmctrl"] + args, stdout=subprocess.PIPE) as p:
                output = p.communicate()[0].decode()[:-1]  # Drop trailing newline
                returncode = p.returncode
        except FileNotFoundError:
            return 1, 'ERROR: Please install wmctrl'

        return returncode, output

    def get_window_list(self, filter_desktop=None):
        """
        Returns a list of windows matching an optional desktop filter, requires C{wmctrl}!

        Each list item consists of: C{[hexid, desktop, hostname, title]}

        Where the C{hexid} is the ID used for some other functions (like L{import -window} from ImageMagick).

        C{desktop} is the number of which desktop (sometimes called workspaces) the item appears upon.

        C{hostname} is the hostname of your computer (I'm not sure why this is included as it seems to be the same for everything I have seen)

        C{title} is the title that you would usually see in your window manager of choice.

        @param filter_desktop: String, (usually 0-n) to filter the windows by. Any window not on the given desktop will not be returned.
        @return: C{[[hexid1, desktop1, hostname1, title1], [hexid2,desktop2,hostname2,title2], ...etc]}
        Returns C{[]} if no windows are found.
        """
        returncode, output = self._run_wmctrl(["-l"])
        # regex = r"^(0x[0-9a-fA-F]{8})  (\d*) (.*?) (.*?)$"
        regex = r"^(0x[0-9a-fA-F]{8})\s*(\d*)\s*(.*?)\s(.*?)$"
        matches = re.findall(regex, output, re.MULTILINE)
        print(matches)
        if filter_desktop is None:
            return matches
        else:
            output = []
            for match in matches:
                hexid, desktop, hostname, window_title = match
                if not filter_desktop==desktop:
                    continue
                output.append((hexid,desktop,hostname, window_title))
            return output

    def get_window_hex(self, window_title):
        """
        Returns the hexid of the first window to match window_title.

        @param window_title: Window title to match for returning hexid
        @return: Returns hexid of the window to be used for other functions See L{get_window_geom}, L{visgrep_by_window_id}

        Returns C{None} if no matches are found
        """
        windowList = self.get_window_list()
        for window in windowList:
            if window_title in window[3]:
                return window[0]
        return None




    def get_window_geom(self, window_id):
        """
        Uses C{wmctrl} to return the window geom of the given window_id. Returns where the location of the 
        top left hand corner of the window is and how long/tall the window is.


        @return: C{[offsetx, offsety, sizex, sizey]} Returns none if no matches are found
        """

        returncode, output = self._run_wmctrl(["-lG"])
        regex = r"^(0x[0-9a-fA-F]{8})\s*(\d*)\s*(\d*)\s*(\d{1,})\s*(\d{1,})\s*(\d{1,})\s*(.*?)$"
        matches = re.findall(regex, output, re.MULTILINE)
        for match in matches:
            if match[0] == window_id:
                return [int(i) for i in match[2:-1]] # trim hexid, gravity on the front end and title on the backend
        return None
