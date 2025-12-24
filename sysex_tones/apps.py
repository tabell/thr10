"""Shared THR10 application behaviors for CLI and examples."""

import errno

import sysex_tones
import sysex_tones.THR

from sysex_tones.THR10 import THR10


def monitor_thr(midi_in):
	"""Monitor incoming MIDI data and print recognized THR messages."""
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
						thr.print_sysex_data(sysex, detected['data'])
					else:
						command = thr.find_thr_command(sysex, context)
						if command:
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
				thr.close_infile()
				thr = None


def view_current_settings(midi_in, midi_out):
	"""Request and display the current THR settings."""
	thr = THR10()
	thr.open_infile_wait_indefinitely(midi_in)
	thr.request_current_settings(midi_out)
	while thr:
		try:
			attempt = thr.extract_dump()
			if attempt:
				thr.print_sysex_data(attempt['sysex'], attempt['dump'])
				thr.close_infile()
				thr = None
		except IOError as error:
			if error.errno == errno.ENODEV:
				thr.close_infile()


def write_config_files(midi_out, config_files):
	"""Send text settings files to the THR device."""
	thr = THR10()
	thr.open_outfile(midi_out)
	for infilename in config_files:
		thr.write_text_to_midi(infilename)
	thr.close_outfile()


def dump_thr_files(input_files):
	"""Convert THR dump or SysEx files into text settings."""
	thr = THR10()
	for infilename in input_files:
		lines = thr.convert_infile_to_text(infilename)
		if lines:
			for line in lines:
				print(line)
		else:
			print('No THR SysEx found.')


def save_settings_dumps(midi_in, midi_out, postfix):
	"""Save any settings dumps to numbered files."""
	thr = THR10(midi_in, midi_out)
	thr.open_infile_wait_indefinitely()
	thr.request_current_settings()
	count = 0
	while thr:
		try:
			attempt = thr.extract_dump()
			if attempt:
				savefilename = '%i_%s' % (count, postfix)
				with open(savefilename, 'wb') as savefile:
					savefile.write(bytearray(attempt['dump']))
				count += 1
		except IOError as error:
			if error.errno == errno.ENODEV:
				thr.close_infile()
				thr = None


def rename_current_settings(midi_in, midi_out, new_name):
	"""Change the name of the current THR settings and write it back."""
	newname = sysex_tones.convert_from_stream(new_name.strip())
	thr = sysex_tones.THR10.THR10(midi_in, midi_out)
	thr.open_infile_wait_indefinitely()
	thr.request_current_settings()
	while thr:
		try:
			attempt = thr.extract_dump()
			if attempt:
				thr.print_sysex_data(attempt['sysex'], attempt['dump'])
				newsysex = sysex_tones.THR.change_name_of_settings(newname, attempt['sysex'])
				detected = thr.detect_midi_dump(newsysex)
				if detected:
					thr.print_sysex_data(newsysex, detected['data'])
					thr.write_data_to_outfile(newsysex)
					thr.close_infile()
					thr = None
					break
		except IOError as error:
			if error.errno == errno.ENODEV and thr:
				thr.close_infile()
				thr = None
