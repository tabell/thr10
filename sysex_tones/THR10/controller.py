"""THR10 controller for live/staged state management."""

import time
from typing import Callable, Optional

import sysex_tones

from sysex_tones.THR10 import THR10 as _THR10
from sysex_tones.THR10 import state as thr10_state


class THR10Controller:
	"""Manage live/staged THR10 state with debounced device writes."""

	def __init__(
		self,
		midi_in: Optional[str] = None,
		midi_out: Optional[str] = None,
		debounce_seconds: float = 0.3,
		poll_interval: float = 0.05,
		clock: Callable[[], float] = time.monotonic,
	):
		self.thr = _THR10( midi_in, midi_out )
		self.live_state = thr10_state.THR10State()
		self.staged_state = thr10_state.THR10State()
		self.conflicts = {}
		self.debounce_seconds = debounce_seconds
		self.poll_interval = poll_interval
		self._clock = clock
		self._last_edit_time = None
		self._pending_apply = False

	def refresh_from_device( self, midi_in=None, midi_out=None, timeout_s: Optional[float] = 1.0 ):
		"""Request and refresh the live state from the THR10 device."""
		if midi_in:
			self.thr.open_infile_wait_indefinitely( midi_in )
		if midi_out or self.thr.outfilename:
			self.thr.request_current_settings( midi_out )
		else:
			self.thr.request_current_settings()
		start = self._clock()
		attempt = None
		while True:
			attempt = self.thr.extract_dump()
			if attempt:
				break
			if timeout_s is None:
				break
			if self._clock() - start >= timeout_s:
				break
			time.sleep( self.poll_interval )
		if not attempt:
			return None
		lines = sysex_tones.THR10.convert_midi_dump_to_text( attempt['dump'] )
		device_state = thr10_state.from_text_settings( lines )
		self._detect_conflicts( device_state )
		self.live_state = device_state
		return device_state

	def apply_staged( self ):
		"""Apply staged settings to the device and refresh live state."""
		diffs = thr10_state.diff_state( self.live_state, self.staged_state )
		if not diffs:
			self._pending_apply = False
			return False
		merged = thr10_state.apply_state( self.live_state, self.staged_state )
		self._write_state( merged )
		self.live_state = merged
		self.staged_state = thr10_state.THR10State()
		self._pending_apply = False
		self.conflicts = {}
		return True

	def discard_staged( self ):
		"""Discard staged edits."""
		self.staged_state = thr10_state.THR10State()
		self._pending_apply = False
		self.conflicts = {}

	def set_param( self, path: str, value ):
		"""Stage a parameter update using a dotted path."""
		self._set_state_value( self.staged_state, path, value )
		self._pending_apply = True
		self._last_edit_time = self._clock()

	def flush_debounced( self, force: bool = False ) -> bool:
		"""Apply staged edits after debounce idle time or when forced."""
		if not self._pending_apply:
			return False
		if force:
			return self.apply_staged()
		if self._last_edit_time is None:
			return False
		if self._clock() - self._last_edit_time < self.debounce_seconds:
			return False
		return self.apply_staged()

	def _write_state( self, state: thr10_state.THR10State ) -> None:
		lines = thr10_state.to_text_settings( state )
		payload = []
		for line in lines:
			command = sysex_tones.THR10.convert_text_to_midi( line )
			if command:
				payload += command
		if payload:
			self.thr.write_data_to_outfile( payload )

	def _detect_conflicts( self, device_state: thr10_state.THR10State ) -> None:
		staged_diffs = thr10_state.diff_state( self.live_state, self.staged_state )
		device_diffs = thr10_state.diff_state( self.live_state, device_state )
		self.conflicts = {}
		if not staged_diffs or not device_diffs:
			return
		for path, staged_diff in staged_diffs.items():
			device_diff = device_diffs.get( path )
			if not device_diff:
				continue
			self.conflicts[path] = {
				'live': staged_diff['live'],
				'staged': staged_diff['staged'],
				'device': device_diff['staged'],
			}

	def _set_state_value( self, state: thr10_state.THR10State, path: str, value ) -> None:
		parts = [part for part in path.replace( '/', '.' ).split( '.' ) if part]
		if not parts:
			raise ValueError( 'Parameter path is empty.' )
		cursor = state
		for part in parts[:-1]:
			name = self._normalize_field( part )
			if not hasattr( cursor, name ):
				raise AttributeError( 'Unknown parameter group: %s' % ( part, ) )
			cursor = getattr( cursor, name )
		last = self._normalize_field( parts[-1] )
		if not hasattr( cursor, last ):
			raise AttributeError( 'Unknown parameter: %s' % ( parts[-1], ) )
		setattr( cursor, last, value )

	@staticmethod
	def _normalize_field( name: str ) -> str:
		return name.strip().lower().replace( ' ', '_' ).replace( '-', '_' )
