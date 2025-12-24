#!/usr/bin/env python
""" Example app that waits indefinitely, listening to the THR device, and saves any settings dumps to files with numbered prefixes.

	Turn the device off when you want to exit the app.
"""

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


def save_settings_dumps( infilename, outfilename, savefilenamepostfix ):
	""" Save settings dumps to N_savefilenamepostfix. """
	thr_apps.save_settings_dumps( infilename, outfilename, savefilenamepostfix )


if __name__ == '__main__':
	if len( sys.argv ) == 4:
		save_settings_dumps( sys.argv[1], sys.argv[2], sys.argv[3] )
	else:
		print( 'Usage: %s MIDIINPUTDEVFILENAME MIDIOUTPUTDEVFILENAME OUTPUTFILENAMEPOSTFIX' % (sys.argv[0]) )
