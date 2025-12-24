"""Shared THR10 application behaviors for CLI and examples."""

import errno
import sys

import sysex_tones
import sysex_tones.THR

from sysex_tones.THR import CONSTANTS as _THR_CONSTANTS
from sysex_tones.THR10 import THR10
from sysex_tones.THR10 import state as thr10_state


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


def _state_from_lines(lines):
	"""Parse text settings into a THR10State."""
	return thr10_state.from_text_settings(lines)


def _state_to_lines(state):
	"""Serialize a THR10State into text settings."""
	return thr10_state.to_text_settings(state)


def _write_text_lines(thr, lines):
	"""Write text settings lines to a THR device."""
	payload = []
	for line in lines:
		command = sysex_tones.THR10.convert_text_to_midi(line)
		if command:
			payload += command
	if payload:
		thr.write_data_to_outfile(payload)


def _replace_dump_data(sysex, data):
	"""Replace the dump data payload in a SysEx dump and refresh the checksum."""
	updated = sysex[:]
	start = _THR_CONSTANTS.THR_DUMP_OFFSET
	end = start + _THR_CONSTANTS.THR_SYSEX_SIZE
	updated[start:end] = data[:_THR_CONSTANTS.THR_SYSEX_SIZE]
	payload_start = len(_THR_CONSTANTS.THR_DUMP_HEADER_PREFIX)
	updated[-2] = sysex_tones.THR.calculate_checksum(updated[payload_start:-2])
	return updated


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
				lines = sysex_tones.THR10.convert_midi_dump_to_text(attempt['dump'])
				state = _state_from_lines(lines)
				for line in _state_to_lines(state):
					print(line)
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
		with open(infilename, 'r', encoding='utf-8', errors='ignore') as infile:
			lines = infile.read().splitlines()
		state = _state_from_lines(lines)
		_write_text_lines(thr, _state_to_lines(state))
	thr.close_outfile()


def dump_thr_files(input_files, verbose=False):
	"""Convert THR dump or SysEx files into text settings."""
	thr = THR10()
	for infilename in input_files:
		_log(verbose, 'Converting file: %s' % (infilename))
		lines = thr.convert_infile_to_text(infilename)
		if lines:
			state = _state_from_lines(lines)
			for line in _state_to_lines(state):
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
	thr = sysex_tones.THR10.THR10(midi_in, midi_out)
	thr.open_infile_wait_indefinitely()
	thr.request_current_settings()
	while thr:
		try:
			attempt = thr.extract_dump()
			if attempt:
				_log(verbose, 'Received settings dump.')
				lines = sysex_tones.THR10.convert_midi_dump_to_text(attempt['dump'])
				state = _state_from_lines(lines)
				for line in _state_to_lines(state):
					print(line)
				state.name = new_name.strip()
				updated_data = thr10_state.to_midi_data(state)
				newsysex = _replace_dump_data(attempt['sysex'], updated_data)
				detected = thr.detect_midi_dump(newsysex)
				if detected:
					_log(verbose, 'Writing renamed settings.')
					for line in _state_to_lines(state):
						print(line)
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
