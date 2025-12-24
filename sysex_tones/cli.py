"""Command-line utilities for THR SysEx operations."""

import argparse
import sys

from sysex_tones import apps as thr_apps


EXAMPLE_TEXT = """
Examples:
  sysex-tones monitor /dev/midi1
  sysex-tones view /dev/midi1 /dev/midi2
  sysex-tones write /dev/midi2 tone1.txt tone2.txt
  sysex-tones dump preset.syx preset2.syx
  sysex-tones save-dumps /dev/midi1 /dev/midi2 preset_dump.syx
  sysex-tones rename /dev/midi1 /dev/midi2 "New Preset"
"""


def _require(value, label):
	"""Raise ValueError if value is missing."""
	if not value:
		raise ValueError('Missing required %s.' % (label))
	return value


def cmd_monitor(args):
	"""Monitor incoming MIDI data and print recognized THR messages."""
	midi_in = _require(args.midi_in, 'MIDI input device filename')
	thr_apps.monitor_thr(midi_in, verbose=args.verbose)
	return 0


def cmd_view(args):
	"""Request and display the current THR settings."""
	midi_in = _require(args.midi_in, 'MIDI input device filename')
	midi_out = _require(args.midi_out, 'MIDI output device filename')
	thr_apps.view_current_settings(midi_in, midi_out, verbose=args.verbose)
	return 0


def cmd_write(args):
	"""Send text settings files to the THR device."""
	midi_out = _require(args.midi_out, 'MIDI output device filename')
	config_files = []
	if args.config_files:
		config_files.extend(args.config_files)
	if args.config_files_opt:
		config_files.extend(args.config_files_opt)
	if not config_files:
		raise ValueError('Missing required config filenames.')
	thr_apps.write_config_files(midi_out, config_files, verbose=args.verbose)
	return 0


def cmd_dump(args):
	"""Convert THR dump or SysEx files into text settings."""
	input_files = []
	if args.input_files:
		input_files.extend(args.input_files)
	if args.input_files_opt:
		input_files.extend(args.input_files_opt)
	if not input_files:
		raise ValueError('Missing required input filenames.')
	thr_apps.dump_thr_files(input_files, verbose=args.verbose)
	return 0


def cmd_save_dumps(args):
	"""Save any settings dumps to numbered files."""
	midi_in = _require(args.midi_in, 'MIDI input device filename')
	midi_out = _require(args.midi_out, 'MIDI output device filename')
	postfix = _require(args.postfix, 'output filename postfix')
	thr_apps.save_settings_dumps(midi_in, midi_out, postfix, verbose=args.verbose)
	return 0


def cmd_rename(args):
	"""Change the name of the current THR settings and write it back."""
	midi_in = _require(args.midi_in, 'MIDI input device filename')
	midi_out = _require(args.midi_out, 'MIDI output device filename')
	new_name = _require(args.new_name, 'new settings name')
	thr_apps.rename_current_settings(midi_in, midi_out, new_name, verbose=args.verbose)
	return 0


def _add_io_arguments(parser, needs_out=False, needs_postfix=False, needs_name=False):
	parser.add_argument('midi_in', nargs='?', help='MIDI input device filename')
	parser.add_argument('--midi-in', dest='midi_in', help='MIDI input device filename')
	if needs_out:
		parser.add_argument('midi_out', nargs='?', help='MIDI output device filename')
		parser.add_argument('--midi-out', dest='midi_out', help='MIDI output device filename')
	if needs_postfix:
		parser.add_argument('postfix', nargs='?', help='Output filename postfix')
		parser.add_argument('--postfix', dest='postfix', help='Output filename postfix')
	if needs_name:
		parser.add_argument('new_name', nargs='?', help='New settings name')
		parser.add_argument('--name', dest='new_name', help='New settings name')


def build_parser():
	"""Build the CLI parser."""
	parent_parser = argparse.ArgumentParser(add_help=False)
	parent_parser.add_argument(
		'-v',
		'--verbose',
		action='store_true',
		help='Enable verbose logging.',
	)

	parser = argparse.ArgumentParser(
		prog='sysex-tones',
		description='Utilities for Yamaha THR10 SysEx operations.',
		epilog=EXAMPLE_TEXT,
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	subparsers = parser.add_subparsers(dest='command', required=True)

	monitor = subparsers.add_parser(
		'monitor',
		aliases=['monitor_thr', 'monitor-thr'],
		parents=[parent_parser],
		help='Monitor incoming MIDI data from the THR device.',
		description='Listen to a MIDI input and print recognized THR commands.',
		epilog='Example: sysex-tones monitor /dev/midi1',
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	_add_io_arguments(monitor)
	monitor.set_defaults(func=cmd_monitor)

	view = subparsers.add_parser(
		'view',
		aliases=['view_current_thr_settings', 'view-current'],
		parents=[parent_parser],
		help='Request and display current THR settings.',
		description='Request the current settings dump and print it.',
		epilog='Example: sysex-tones view /dev/midi1 /dev/midi2',
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	_add_io_arguments(view, needs_out=True)
	view.set_defaults(func=cmd_view)

	write = subparsers.add_parser(
		'write',
		aliases=['write_config_files_to_thr', 'write-config'],
		parents=[parent_parser],
		help='Send text settings files to the THR device.',
		description='Convert text settings files into MIDI data and send them.',
		epilog='Example: sysex-tones write /dev/midi2 tone1.txt tone2.txt',
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	write.add_argument('midi_out', nargs='?', help='MIDI output device filename')
	write.add_argument('--midi-out', dest='midi_out', help='MIDI output device filename')
	write.add_argument('config_files', nargs='*', help='Config text files to send')
	write.add_argument(
		'--config',
		dest='config_files_opt',
		action='append',
		help='Config text file to send (repeatable)',
	)
	write.set_defaults(func=cmd_write)

	dump_cmd = subparsers.add_parser(
		'dump',
		aliases=['dump_thr_files', 'dump-files'],
		parents=[parent_parser],
		help='Convert THR dump or SysEx files into text.',
		description='Display text conversions of THR settings or SysEx files.',
		epilog='Example: sysex-tones dump preset.syx',
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	dump_cmd.add_argument('input_files', nargs='*', help='Input dump/SysEx files')
	dump_cmd.add_argument(
		'--input',
		dest='input_files_opt',
		action='append',
		help='Input file to convert (repeatable)',
	)
	dump_cmd.set_defaults(func=cmd_dump)

	save = subparsers.add_parser(
		'save-dumps',
		aliases=['save_any_dumped_thr_settings', 'save-dumped'],
		parents=[parent_parser],
		help='Save any settings dumps to numbered files.',
		description='Save settings dumps received from the THR device.',
		epilog='Example: sysex-tones save-dumps /dev/midi1 /dev/midi2 preset.syx',
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	_add_io_arguments(save, needs_out=True, needs_postfix=True)
	save.set_defaults(func=cmd_save_dumps)

	rename = subparsers.add_parser(
		'rename',
		aliases=['change_name_of_current_settings_on_thr', 'change-name'],
		parents=[parent_parser],
		help='Change the name of the current THR settings.',
		description='Read current settings, change the name, and write it back.',
		epilog='Example: sysex-tones rename /dev/midi1 /dev/midi2 "New Preset"',
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	_add_io_arguments(rename, needs_out=True, needs_name=True)
	rename.set_defaults(func=cmd_rename)

	return parser


def main(argv=None):
	"""Run the CLI."""
	parser = build_parser()
	args = parser.parse_args(argv)
	try:
		return args.func(args)
	except ValueError as error:
		print('Error: %s' % (error), file=sys.stderr)
		return 2
	except Exception as error:
		print('Error: %s' % (error), file=sys.stderr)
		return 1


if __name__ == '__main__':
	sys.exit(main())
