#!/usr/bin/env python
""" Example app that reads the current THR device settings, changes the name of the settings, and writes it back to the device. """

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


def change_settings_name( infilename, outfilename, newsettingsname ):
	""" Ask the THR device for a settings dump, change the name in it, and write it back to the device. """
	thr_apps.rename_current_settings( infilename, outfilename, newsettingsname )


if __name__ == '__main__':
	if len( sys.argv ) == 4:
		change_settings_name( sys.argv[1], sys.argv[2], sys.argv[3] )
	else:
		print( 'Usage: %s MIDIINPUTDEVFILENAME MIDIOUTPUTDEVFILENAME "new settings name"' % (sys.argv[0]) )
