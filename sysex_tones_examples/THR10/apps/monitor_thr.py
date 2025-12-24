#!/usr/bin/env python
""" Example app that listens for MIDI from the THR device, displaying any recognized MIDI as settings text.

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


def process_file( infilename ):
	""" Listen to the THR device via the infilename, output any data sent by the device. """
	thr_apps.monitor_thr( infilename )


if __name__ == '__main__':
	if len( sys.argv ) > 1:
		process_file( sys.argv[1] )
	else:
		print( 'Usage: %s MIDIINPUTDEVFILENAME' % (sys.argv[0]) )
