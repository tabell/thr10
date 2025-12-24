#!/usr/bin/env python
""" Example application that requests the current settings from a THR10 and prints the results. """

# Copyright (c) 2016
#
# This project is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This project is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.


import sys
from sysex_tones import apps as thr_apps


def view_current_settings( infilename, outfilename ):
	""" View the current device settings. """
	thr_apps.view_current_settings( infilename, outfilename )


if __name__ == '__main__':
	if len( sys.argv ) == 3:
		view_current_settings( sys.argv[1], sys.argv[2] )
	else:
		print( 'Usage: %s MIDIINPUTDEVFILENAME MIDIOUTPUTDEVFILENAME' % (sys.argv[0]) )
