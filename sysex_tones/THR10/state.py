"""Structured THR10 state helpers."""

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


from dataclasses import dataclass, field, fields, is_dataclass
import struct as _struct
from typing import Iterable, Optional

import sysex_tones as _sysex_tones

from sysex_tones.THR import CONSTANTS as _THR_CONSTANTS
from sysex_tones.THR10 import CONSTANTS as _THR10_CONSTANTS
from sysex_tones.THR10 import convert_data as _convert_data


_AMP_INDEX = 128
_CONTROL_INDICES = {
	'gain': 129,
	'master': 130,
	'bass': 131,
	'middle': 132,
	'treble': 133,
}
_CAB_INDEX = 134

_COMPRESSOR_TYPE_INDEX = 144
_COMPRESSOR_STOMP_SUSTAIN_INDEX = 145
_COMPRESSOR_STOMP_OUTPUT_INDEX = 146
_COMPRESSOR_RACK_THRESHOLD_INDEX = 146
_COMPRESSOR_RACK_ATTACK_INDEX = 147
_COMPRESSOR_RACK_RELEASE_INDEX = 148
_COMPRESSOR_RACK_RATIO_INDEX = 149
_COMPRESSOR_RACK_KNEE_INDEX = 150
_COMPRESSOR_RACK_OUTPUT_INDEX = 151
_COMPRESSOR_ON_INDEX = 159

_MODULATION_TYPE_INDEX = 160
_MODULATION_SPEED_INDEX = 161
_MODULATION_MANUAL_INDEX = 162
_MODULATION_DEPTH_CHORUS_INDEX = 162
_MODULATION_DEPTH_INDEX = 163
_MODULATION_MIX_INDEX = 163
_MODULATION_FEEDBACK_INDEX = 164
_MODULATION_SPREAD_INDEX = 165
_MODULATION_ON_INDEX = 175

_DELAY_TIME_INDEX = 177
_DELAY_FEEDBACK_INDEX = 179
_DELAY_HIGH_CUT_INDEX = 180
_DELAY_LOW_CUT_INDEX = 182
_DELAY_LEVEL_INDEX = 184
_DELAY_ON_INDEX = 191

_REVERB_TYPE_INDEX = 192
_REVERB_TIME_INDEX = 193
_REVERB_PRE_INDEX = 195
_REVERB_LOW_CUT_INDEX = 197
_REVERB_HIGH_CUT_INDEX = 199
_REVERB_HIGH_RATIO_INDEX = 201
_REVERB_LOW_RATIO_INDEX = 202
_REVERB_LEVEL_INDEX = 203
_REVERB_SPRING_REVERB_INDEX = 193
_REVERB_SPRING_FILTER_INDEX = 194
_REVERB_ON_INDEX = 207

_GATE_THRESHOLD_INDEX = 209
_GATE_RELEASE_INDEX = 210
_GATE_ON_INDEX = 223


@dataclass
class AmpState:
	model: Optional[str] = None
	gain: Optional[int] = None
	master: Optional[int] = None
	bass: Optional[int] = None
	middle: Optional[int] = None
	treble: Optional[int] = None


@dataclass
class CabState:
	model: Optional[str] = None


@dataclass
class CompressorState:
	on: Optional[bool] = None
	kind: Optional[str] = None
	sustain: Optional[int] = None
	output: Optional[int] = None
	threshold: Optional[int] = None
	attack: Optional[int] = None
	release: Optional[int] = None
	ratio: Optional[str] = None
	knee: Optional[str] = None


@dataclass
class ModulationState:
	on: Optional[bool] = None
	kind: Optional[str] = None
	speed: Optional[int] = None
	depth: Optional[int] = None
	mix: Optional[int] = None
	manual: Optional[int] = None
	feedback: Optional[int] = None
	spread: Optional[int] = None
	freq: Optional[int] = None


@dataclass
class DelayState:
	on: Optional[bool] = None
	time: Optional[int] = None
	feedback: Optional[int] = None
	high_cut: Optional[int] = None
	low_cut: Optional[int] = None
	level: Optional[int] = None


@dataclass
class ReverbState:
	on: Optional[bool] = None
	kind: Optional[str] = None
	time: Optional[int] = None
	pre: Optional[int] = None
	low_cut: Optional[int] = None
	high_cut: Optional[int] = None
	high_ratio: Optional[int] = None
	low_ratio: Optional[int] = None
	level: Optional[int] = None
	reverb: Optional[int] = None
	filter: Optional[int] = None


@dataclass
class GateState:
	on: Optional[bool] = None
	threshold: Optional[int] = None
	release: Optional[int] = None


@dataclass
class THR10State:
	name: Optional[str] = None
	edited: Optional[bool] = None
	stored: Optional[bool] = None
	amp: AmpState = field(default_factory=AmpState)
	cab: CabState = field(default_factory=CabState)
	compressor: CompressorState = field(default_factory=CompressorState)
	modulation: ModulationState = field(default_factory=ModulationState)
	delay: DelayState = field(default_factory=DelayState)
	reverb: ReverbState = field(default_factory=ReverbState)
	gate: GateState = field(default_factory=GateState)


def from_text_settings( lines: Iterable[str] ) -> THR10State:
	"""Parse text settings strings into a THR10State."""
	state = THR10State()
	if lines is None:
		return state
	if isinstance( lines, (bytes, bytearray) ):
		lines = lines.decode( 'utf-8', errors='ignore' ).splitlines()
	elif isinstance( lines, str ):
		lines = lines.splitlines()
	for line in lines:
		if isinstance( line, (bytes, bytearray) ):
			line = line.decode( 'utf-8', errors='ignore' )
		text = line.strip()
		if not text or text.startswith( '#' ):
			continue
		(setting, valuelist, values) = _sysex_tones.extract_settings( text )
		if not setting:
			continue
		if setting == 'name':
			state.name = valuelist.strip()
			continue
		if setting in ('edited', 'edit'):
			state.edited = _parse_on_off( values )
			continue
		if setting == 'stored':
			state.stored = _parse_on_off( values )
			continue
		if setting == 'amp':
			state.amp.model = _canonical_option( _first_key( values ), _THR10_CONSTANTS.THR10_AMP_NAMES )
			continue
		if setting == 'control':
			_assign_int_fields( state.amp, values, ['gain', 'master', 'bass', 'middle', 'treble'] )
			continue
		if setting == 'cab':
			state.cab.model = _canonical_option( _first_key( values ), _THR10_CONSTANTS.THR10_CAB_NAMES )
			continue
		if setting == 'compressor':
			state.compressor.on = _merge_bool( state.compressor.on, _parse_on_off( values ) )
			compressor_type = _first_match( values, _THR10_CONSTANTS.THR10_COMPRESSOR_NAMES )
			if compressor_type:
				state.compressor.kind = compressor_type
			_assign_int_fields( state.compressor, values, ['sustain', 'output', 'threshold', 'attack', 'release'] )
			state.compressor.ratio = _canonical_option( _value_or_key( values, 'ratio' ), _THR10_CONSTANTS.THR10_RATIO_NAMES )
			state.compressor.knee = _canonical_option( _value_or_key( values, 'knee' ), _THR10_CONSTANTS.THR10_KNEE_NAMES )
			continue
		if setting == 'modulation':
			state.modulation.on = _merge_bool( state.modulation.on, _parse_on_off( values ) )
			modulation_type = _first_match( values, _THR10_CONSTANTS.THR10_MODULATION_NAMES )
			if modulation_type:
				state.modulation.kind = modulation_type
			_assign_int_fields( state.modulation, values, ['speed', 'depth', 'mix', 'manual', 'feedback', 'spread', 'freq'] )
			continue
		if setting == 'delay':
			state.delay.on = _merge_bool( state.delay.on, _parse_on_off( values ) )
			_assign_int_fields( state.delay, values, ['time', 'feedback', 'high cut', 'low cut', 'level'] )
			continue
		if setting == 'reverb':
			state.reverb.on = _merge_bool( state.reverb.on, _parse_on_off( values ) )
			reverb_type = _first_match( values, _THR10_CONSTANTS.THR10_REVERB_NAMES )
			if reverb_type:
				state.reverb.kind = reverb_type
			_assign_int_fields( state.reverb, values, ['time', 'pre', 'low cut', 'high cut', 'high ratio', 'low ratio', 'level', 'reverb', 'filter'] )
			continue
		if setting == 'gate':
			state.gate.on = _merge_bool( state.gate.on, _parse_on_off( values ) )
			_assign_int_fields( state.gate, values, ['threshold', 'release'] )
			continue
	return state


def to_text_settings( state: THR10State ) -> list[str]:
	"""Serialize a THR10State into text settings strings."""
	data = _state_to_data( state )
	comment = '# '
	retval = [
		_convert_data.name_data_to_string( data ),
	]
	if state.edited is not None:
		retval.append( _boolean_setting_to_string( 'Edited', state.edited ) )
	if state.stored is not None:
		retval.append( _boolean_setting_to_string( 'Stored', state.stored ) )
	retval.append( _convert_data.amp_data_to_string( data, comment ) )
	retval.append( _convert_data.control_data_to_string( data ) )
	retval.append( _convert_data.cab_data_to_string( data, comment ) )
	retval += _convert_data.compressor_data_to_strings( data, comment )
	retval += _convert_data.modulation_data_to_strings( data, comment )
	retval += _convert_data.delay_data_to_strings( data, comment )
	retval += _convert_data.reverb_data_to_strings( data, comment )
	retval += _convert_data.gate_data_to_strings( data, comment )
	return retval


def to_midi_data( state: THR10State ) -> list:
	"""Serialize a THR10State into raw THR10 settings data."""
	return _state_to_data( state )


def diff_state( live: THR10State, staged: THR10State ) -> dict:
	"""Return a dictionary of differences between live and staged state."""
	diffs = {}
	_diff_values( live, staged, '', diffs )
	return diffs


def apply_state( live: THR10State, staged: THR10State ) -> THR10State:
	"""Merge staged changes onto live state, preserving live defaults."""
	return _merge_dataclasses( live, staged )


def merge_state( live: THR10State, staged: THR10State ) -> THR10State:
	"""Alias for apply_state for callers that prefer merge semantics."""
	return apply_state( live, staged )


def _state_to_data( state: THR10State ) -> list:
	data = [0] * _THR_CONSTANTS.THR_SYSEX_SIZE
	_apply_name( data, state.name )
	_apply_amp( data, state.amp )
	_apply_cab( data, state.cab )
	_apply_compressor( data, state.compressor )
	_apply_modulation( data, state.modulation )
	_apply_delay( data, state.delay )
	_apply_reverb( data, state.reverb )
	_apply_gate( data, state.gate )
	return data


def _apply_name( data: list, name: Optional[str] ) -> None:
	if not name:
		return
	name_bytes = name.encode( 'ascii', errors='ignore' )[:_THR_CONSTANTS.THR_SETTINGS_NAME_SIZE]
	for index in range( _THR_CONSTANTS.THR_SETTINGS_NAME_SIZE ):
		data[index] = 0
	for index, val in enumerate( name_bytes ):
		data[index] = val


def _apply_amp( data: list, amp: AmpState ) -> None:
	index = _option_index( amp.model, _THR10_CONSTANTS.THR10_AMP_NAMES, default=0 )
	data[_AMP_INDEX] = index
	for key, idx in _CONTROL_INDICES.items():
		limits = _THR10_CONSTANTS.THR10_STREAM_LIMITS['control'][key]
		value = getattr( amp, key )
		data[idx] = _limit_value( value, limits )


def _apply_cab( data: list, cab: CabState ) -> None:
	index = _option_index( cab.model, _THR10_CONSTANTS.THR10_CAB_NAMES, default=0 )
	data[_CAB_INDEX] = index


def _apply_compressor( data: list, compressor: CompressorState ) -> None:
	kind = _infer_compressor_kind( compressor )
	kind_index = _option_index( kind, _THR10_CONSTANTS.THR10_COMPRESSOR_NAMES, default=0 )
	data[_COMPRESSOR_TYPE_INDEX] = kind_index
	data[_COMPRESSOR_ON_INDEX] = _on_off_value( compressor.on )
	if kind_index == 0:
		limits = _THR10_CONSTANTS.THR10_STREAM_SUBLIMITS['stomp']
		data[_COMPRESSOR_STOMP_SUSTAIN_INDEX] = _limit_value( compressor.sustain, limits['sustain'] )
		data[_COMPRESSOR_STOMP_OUTPUT_INDEX] = _limit_value( compressor.output, limits['output'] )
	else:
		limits = _THR10_CONSTANTS.THR10_STREAM_SUBLIMITS['rack']
		_set_midi_int( data, _COMPRESSOR_RACK_THRESHOLD_INDEX, _limit_value( compressor.threshold, limits['threshold'] ) )
		data[_COMPRESSOR_RACK_ATTACK_INDEX] = _limit_value( compressor.attack, limits['attack'] )
		data[_COMPRESSOR_RACK_RELEASE_INDEX] = _limit_value( compressor.release, limits['release'] )
		data[_COMPRESSOR_RACK_RATIO_INDEX] = _option_index( compressor.ratio, _THR10_CONSTANTS.THR10_RATIO_NAMES, default=0 )
		data[_COMPRESSOR_RACK_KNEE_INDEX] = _option_index( compressor.knee, _THR10_CONSTANTS.THR10_KNEE_NAMES, default=0 )
		_set_midi_int( data, _COMPRESSOR_RACK_OUTPUT_INDEX, _limit_value( compressor.output, limits['output'] ) )


def _apply_modulation( data: list, modulation: ModulationState ) -> None:
	kind = _infer_modulation_kind( modulation )
	kind_index = _option_index( kind, _THR10_CONSTANTS.THR10_MODULATION_NAMES, default=0 )
	data[_MODULATION_TYPE_INDEX] = kind_index
	data[_MODULATION_ON_INDEX] = _on_off_value( modulation.on )
	if kind_index == 0:
		limits = _THR10_CONSTANTS.THR10_STREAM_SUBLIMITS['chorus']
		data[_MODULATION_SPEED_INDEX] = _limit_value( modulation.speed, limits['speed'] )
		data[_MODULATION_DEPTH_CHORUS_INDEX] = _limit_value( modulation.depth, limits['depth'] )
		data[_MODULATION_MIX_INDEX] = _limit_value( modulation.mix, limits['mix'] )
	elif kind_index == 1:
		limits = _THR10_CONSTANTS.THR10_STREAM_SUBLIMITS['flanger']
		data[_MODULATION_SPEED_INDEX] = _limit_value( modulation.speed, limits['speed'] )
		data[_MODULATION_MANUAL_INDEX] = _limit_value( modulation.manual, limits['manual'] )
		data[_MODULATION_DEPTH_INDEX] = _limit_value( modulation.depth, limits['depth'] )
		data[_MODULATION_FEEDBACK_INDEX] = _limit_value( modulation.feedback, limits['feedback'] )
		data[_MODULATION_SPREAD_INDEX] = _limit_value( modulation.spread, limits['spread'] )
	elif kind_index == 2:
		limits = _THR10_CONSTANTS.THR10_STREAM_SUBLIMITS['tremelo']
		data[_MODULATION_SPEED_INDEX] = _limit_value( modulation.freq, limits['freq'] )
		data[_MODULATION_DEPTH_CHORUS_INDEX] = _limit_value( modulation.depth, limits['depth'] )
	else:
		limits = _THR10_CONSTANTS.THR10_STREAM_SUBLIMITS['phaser']
		data[_MODULATION_SPEED_INDEX] = _limit_value( modulation.speed, limits['speed'] )
		data[_MODULATION_MANUAL_INDEX] = _limit_value( modulation.manual, limits['manual'] )
		data[_MODULATION_DEPTH_INDEX] = _limit_value( modulation.depth, limits['depth'] )
		data[_MODULATION_FEEDBACK_INDEX] = _limit_value( modulation.feedback, limits['feedback'] )


def _apply_delay( data: list, delay: DelayState ) -> None:
	limits = _THR10_CONSTANTS.THR10_STREAM_LIMITS['delay']
	data[_DELAY_ON_INDEX] = _on_off_value( delay.on )
	_set_midi_int( data, _DELAY_TIME_INDEX, _limit_value( delay.time, limits['time'] ) )
	data[_DELAY_FEEDBACK_INDEX] = _limit_value( delay.feedback, limits['feedback'] )
	_set_midi_int( data, _DELAY_HIGH_CUT_INDEX, _limit_value( delay.high_cut, limits['high cut'] ) )
	_set_midi_int( data, _DELAY_LOW_CUT_INDEX, _limit_value( delay.low_cut, limits['low cut'] ) )
	data[_DELAY_LEVEL_INDEX] = _limit_value( delay.level, limits['level'] )


def _apply_reverb( data: list, reverb: ReverbState ) -> None:
	kind = _infer_reverb_kind( reverb )
	kind_index = _option_index( kind, _THR10_CONSTANTS.THR10_REVERB_NAMES, default=0 )
	data[_REVERB_TYPE_INDEX] = kind_index
	data[_REVERB_ON_INDEX] = _on_off_value( reverb.on )
	if kind_index in [0, 1, 2]:
		limits = _THR10_CONSTANTS.THR10_STREAM_LIMITS['reverb']
		_set_midi_int( data, _REVERB_TIME_INDEX, _limit_value( reverb.time, limits['time'] ) )
		_set_midi_int( data, _REVERB_PRE_INDEX, _limit_value( reverb.pre, limits['pre'] ) )
		_set_midi_int( data, _REVERB_LOW_CUT_INDEX, _limit_value( reverb.low_cut, limits['low cut'] ) )
		_set_midi_int( data, _REVERB_HIGH_CUT_INDEX, _limit_value( reverb.high_cut, limits['high cut'] ) )
		data[_REVERB_HIGH_RATIO_INDEX] = _limit_value( reverb.high_ratio, limits['high ratio'] )
		data[_REVERB_LOW_RATIO_INDEX] = _limit_value( reverb.low_ratio, limits['low ratio'] )
		data[_REVERB_LEVEL_INDEX] = _limit_value( reverb.level, limits['level'] )
	else:
		limits = _THR10_CONSTANTS.THR10_STREAM_LIMITS['reverb']
		data[_REVERB_SPRING_REVERB_INDEX] = _limit_value( reverb.reverb, limits['reverb'] )
		data[_REVERB_SPRING_FILTER_INDEX] = _limit_value( reverb.filter, limits['filter'] )


def _apply_gate( data: list, gate: GateState ) -> None:
	limits = _THR10_CONSTANTS.THR10_STREAM_LIMITS['gate']
	data[_GATE_ON_INDEX] = _on_off_value( gate.on )
	data[_GATE_THRESHOLD_INDEX] = _limit_value( gate.threshold, limits['threshold'] )
	data[_GATE_RELEASE_INDEX] = _limit_value( gate.release, limits['release'] )


def _encode_midi_int( value: int ) -> list:
	vab = _struct.pack( '!I', _sysex_tones.convert_to_midi_int( value ) )
	return [vab[2], vab[3]]


def _set_midi_int( data: list, start_index: int, value: int ) -> None:
	encoded = _encode_midi_int( value )
	data[start_index] = encoded[0]
	data[start_index + 1] = encoded[1]


def _limit_value( value: Optional[int], limits: list[int] ) -> int:
	if value is None:
		value = limits[0]
	return _sysex_tones.get_minmax( value, limits[0], limits[1] )


def _option_index( value: Optional[str], options: list[str], default: int = 0 ) -> int:
	if value is None:
		return default
	if isinstance( value, int ):
		return _sysex_tones.get_minmax( value, 0, len( options ) - 1 )
	value_lower = value.lower()
	for index, option in enumerate( options ):
		if option.lower() == value_lower:
			return index
	return default


def _canonical_option( value: Optional[str], options: list[str] ) -> Optional[str]:
	if not value:
		return None
	value_lower = value.lower()
	for option in options:
		if option.lower() == value_lower:
			return option
	return value


def _on_off_value( value: Optional[bool] ) -> int:
	if value:
		return 0x00
	return 0x7f


def _parse_on_off( values: dict ) -> Optional[bool]:
	if 'on' in values:
		return True
	if 'off' in values:
		return False
	return None


def _first_key( values: dict ) -> Optional[str]:
	for key in values.keys():
		return key
	return None


def _first_match( values: dict, options: list[str] ) -> Optional[str]:
	lowered = {option.lower(): option for option in options}
	for key in values.keys():
		if key in lowered:
			return lowered[key]
	return None


def _value_or_key( values: dict, key: str ) -> Optional[str]:
	if key in values:
		value = values[key]
		if value is None:
			return key
		return value
	return None


def _merge_bool( existing: Optional[bool], incoming: Optional[bool] ) -> Optional[bool]:
	return incoming if incoming is not None else existing


def _assign_int_fields( target, values: dict, keys: list[str] ) -> None:
	for key in keys:
		if key in values:
			setattr( target, key.replace( ' ', '_' ), values[key] )


def _infer_compressor_kind( compressor: CompressorState ) -> str:
	if compressor.kind:
		return compressor.kind
	if any( val is not None for val in [compressor.threshold, compressor.attack, compressor.release, compressor.ratio, compressor.knee] ):
		return 'Rack'
	if compressor.sustain is not None or compressor.output is not None:
		return 'Stomp'
	return 'Stomp'


def _infer_modulation_kind( modulation: ModulationState ) -> str:
	if modulation.kind:
		return modulation.kind
	if modulation.spread is not None or modulation.manual is not None:
		return 'Flanger'
	if modulation.freq is not None:
		return 'Tremelo'
	if modulation.feedback is not None:
		return 'Phaser'
	if modulation.mix is not None:
		return 'Chorus'
	return 'Chorus'


def _infer_reverb_kind( reverb: ReverbState ) -> str:
	if reverb.kind:
		return reverb.kind
	if reverb.reverb is not None or reverb.filter is not None:
		return 'Spring'
	return 'Hall'


def _boolean_setting_to_string( label: str, value: bool ) -> str:
	return '%s: %s' % (label, _sysex_tones.ternary_operator( value, 'On', 'Off' ))


def _diff_values( live, staged, path: str, diffs: dict ) -> None:
	if staged is None:
		return
	if is_dataclass( staged ):
		live_value = live if is_dataclass( live ) else None
		for field_item in fields( staged ):
			field_name = field_item.name
			next_path = '%s.%s' % (path, field_name) if path else field_name
			_diff_values( getattr( live_value, field_name, None ), getattr( staged, field_name ), next_path, diffs )
		return
	if isinstance( staged, dict ):
		live_dict = live or {}
		for key, value in staged.items():
			next_path = '%s.%s' % (path, key) if path else str( key )
			_diff_values( live_dict.get( key ), value, next_path, diffs )
		return
	if live != staged:
		diffs[path] = {'live': live, 'staged': staged}


def _merge_dataclasses( live, staged ):
	if staged is None:
		return live
	if live is None:
		return staged
	if is_dataclass( staged ):
		kwargs = {}
		for field_item in fields( staged ):
			name = field_item.name
			kwargs[name] = _merge_dataclasses( getattr( live, name, None ), getattr( staged, name, None ) )
		return staged.__class__( **kwargs )
	if isinstance( staged, dict ):
		merged = dict( live or {} )
		for key, value in staged.items():
			merged[key] = _merge_dataclasses( merged.get( key ), value )
		return merged
	return staged if staged is not None else live
