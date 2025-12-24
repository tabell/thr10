"""Shared THR10 application behaviors for CLI and examples."""

import errno
import sys

import sysex_tones
import sysex_tones.THR

from sysex_tones.THR10 import THR10


USAGE_TEXT = """Usage:
  apps.py monitor MIDIINPUTDEVFILENAME
  apps.py view MIDIINPUTDEVFILENAME MIDIOUTPUTDEVFILENAME
  apps.py write MIDIOUTPUTDEVFILENAME CONFIGFILE...
  apps.py dump INPUTFILE...
  apps.py save-dumps MIDIINPUTDEVFILENAME MIDIOUTPUTDEVFILENAME OUTPUTFILENAMEPOSTFIX
  apps.py rename MIDIINPUTDEVFILENAME MIDIOUTPUTDEVFILENAME "new settings name"
"""


def _log(verbose, message):
	"""Print a message when verbose logging is enabled."""
	if verbose:
		print(message)


def monitor_thr(midi_in, verbose=False):
	"""Monitor incoming MIDI data and print recognized THR messages."""
	_log(verbose, 'Opening MIDI input: %s' % (midi_in))
	thr = THR10()
	thr.open_infile_wait_indefinitely(midi_in)
	recognized = [sysex_tones.THR.CONSTANTS.THR10_MODEL_NAME]
	model = ''
	context = ''
	while thr:
		try:
			for sysex in thr.extract_sysex_from_infile():
				heartbeat = thr.find_thr_heartbeat_model(sysex)
				if heartbeat:
					if not model:
						model = heartbeat
						print('Model %s' % (model))
						if model not in recognized:
							print('%s are not recognized.' % (model))
				else:
					detected = thr.detect_midi_dump(sysex)
					if detected:
						_log(verbose, 'Detected settings dump.')
						thr.print_sysex_data(sysex, detected['data'])
					else:
						command = thr.find_thr_command(sysex, context)
						if command:
							_log(verbose, 'Detected THR command.')
							print('THR command', command)
							if 'context' in command:
								context = command['context']
						else:
							print(
								'unrecognized',
								context,
								sysex_tones.convert_bytes_to_hex_string(sysex),
							)
		except IOError as error:
			if error.errno != errno.EAGAIN:
				_log(verbose, 'MIDI input closed.')
				thr.close_infile()
				thr = None


def view_current_settings(midi_in, midi_out, verbose=False):
	"""Request and display the current THR settings."""
	_log(verbose, 'Opening MIDI input: %s' % (midi_in))
	_log(verbose, 'Requesting current settings via: %s' % (midi_out))
	thr = THR10()
	thr.open_infile_wait_indefinitely(midi_in)
	thr.request_current_settings(midi_out)
	while thr:
		try:
			attempt = thr.extract_dump()
			if attempt:
				_log(verbose, 'Received settings dump.')
				thr.print_sysex_data(attempt['sysex'], attempt['dump'])
				thr.close_infile()
				thr = None
		except IOError as error:
			if error.errno == errno.ENODEV:
				_log(verbose, 'MIDI device disconnected.')
				thr.close_infile()


def write_config_files(midi_out, config_files, verbose=False):
	"""Send text settings files to the THR device."""
	_log(verbose, 'Opening MIDI output: %s' % (midi_out))
	thr = THR10()
	thr.open_outfile(midi_out)
	for infilename in config_files:
		_log(verbose, 'Writing config: %s' % (infilename))
		thr.write_text_to_midi(infilename)
	thr.close_outfile()


def dump_thr_files(input_files, verbose=False):
	"""Convert THR dump or SysEx files into text settings."""
	thr = THR10()
	for infilename in input_files:
		_log(verbose, 'Converting file: %s' % (infilename))
		lines = thr.convert_infile_to_text(infilename)
		if lines:
			for line in lines:
				print(line)
		else:
			print('No THR SysEx found.')


def save_settings_dumps(midi_in, midi_out, postfix, verbose=False):
	"""Save any settings dumps to numbered files."""
	_log(verbose, 'Opening MIDI input: %s' % (midi_in))
	_log(verbose, 'Opening MIDI output: %s' % (midi_out))
	thr = THR10(midi_in, midi_out)
	thr.open_infile_wait_indefinitely()
	thr.request_current_settings()
	count = 0
	while thr:
		try:
			attempt = thr.extract_dump()
			if attempt:
				savefilename = '%i_%s' % (count, postfix)
				_log(verbose, 'Saving dump to %s' % (savefilename))
				with open(savefilename, 'wb') as savefile:
					savefile.write(bytearray(attempt['dump']))
				count += 1
		except IOError as error:
			if error.errno == errno.ENODEV:
				_log(verbose, 'MIDI device disconnected.')
				thr.close_infile()
				thr = None


def rename_current_settings(midi_in, midi_out, new_name, verbose=False):
	"""Change the name of the current THR settings and write it back."""
	_log(verbose, 'Opening MIDI input: %s' % (midi_in))
	_log(verbose, 'Opening MIDI output: %s' % (midi_out))
	_log(verbose, 'Renaming settings to: %s' % (new_name))
	newname = sysex_tones.convert_from_stream(new_name.strip())
	thr = sysex_tones.THR10.THR10(midi_in, midi_out)
	thr.open_infile_wait_indefinitely()
	thr.request_current_settings()
	while thr:
		try:
			attempt = thr.extract_dump()
			if attempt:
				_log(verbose, 'Received settings dump.')
				thr.print_sysex_data(attempt['sysex'], attempt['dump'])
				newsysex = sysex_tones.THR.change_name_of_settings(newname, attempt['sysex'])
				detected = thr.detect_midi_dump(newsysex)
				if detected:
					_log(verbose, 'Writing renamed settings.')
					thr.print_sysex_data(newsysex, detected['data'])
					thr.write_data_to_outfile(newsysex)
					thr.close_infile()
					thr = None
					break
		except IOError as error:
			if error.errno == errno.ENODEV and thr:
				_log(verbose, 'MIDI device disconnected.')
				thr.close_infile()
				thr = None


def main(argv=None):
	"""Minimal dispatcher for apps.py when invoked directly."""
	if argv is None:
		argv = sys.argv[1:]
	if not argv:
		print(USAGE_TEXT, file=sys.stderr)
		return 2
	command = argv[0]
	args = argv[1:]
	if command == 'monitor' and len(args) == 1:
		monitor_thr(args[0])
		return 0
	if command == 'view' and len(args) == 2:
		view_current_settings(args[0], args[1])
		return 0
	if command == 'write' and len(args) >= 2:
		write_config_files(args[0], args[1:])
		return 0
	if command == 'dump' and len(args) >= 1:
		dump_thr_files(args)
		return 0
	if command == 'save-dumps' and len(args) == 3:
		save_settings_dumps(args[0], args[1], args[2])
		return 0
	if command == 'rename' and len(args) == 3:
		rename_current_settings(args[0], args[1], args[2])
		return 0
	print(USAGE_TEXT, file=sys.stderr)
	return 2


if __name__ == '__main__':
	sys.exit(main())
