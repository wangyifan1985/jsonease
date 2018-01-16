#!/usr/bin/env python
# coding: utf-8

import re
import uuid
import inspect
from io import StringIO
from datetime import date, time, datetime, timezone, timedelta
from collections import abc
from typing import List, Dict, Any, TextIO, Type, Union, Tuple, Iterable, Mapping

"""
    JSON tools for format, encode and decode, inspired by simplejson.

    +-------------+-------------------+-------------------------+-------------------------------------------+
    | JSON        | Python(Basic)     | Python(Advanced)        | Python(Custom)                            |
    +=============+===================+=========================+===========================================+
    | object      | dict              | mapping, complex, slice | mapping, complex, user-defined type       |
    +-------------+-------------------+-------------------------+-------------------------------------------+
    | array       | list              | sequence, set           | sequence, set                             |
    +-------------+-------------------+-------------------------+-------------------------------------------+
    | string      | str               | str, date, time, uuid   | str, date, time, uuid                     |
    +-------------+-------------------+-------------------------+-------------------------------------------+
    | number      | int, float        | int, float              | int, float                                |
    +-------------+-------------------+-------------------------+-------------------------------------------+
    | true        | true              | true                    | true                                      |
    +-------------+-------------------+-------------------------+-------------------------------------------+
    | false       | False             | False                   | False                                     |
    +-------------+-------------------+-------------------------+-------------------------------------------+
    | null        | None              | None                    | None                                      |
    +-------------+-------------------+-------------------------+-------------------------------------------+
"""


__all__ = ['dump', 'dumps', 'load', 'loads', 'Encoder', 'Decoder', 'Formatter']

__author__ = ['Yifan Wang <yifan_wang@silanis.com>']
__copyright__ = "Copyright (C) 2017, Yifan WANG"
__license__ = "MIT"
__version__ = '2017.11.3'
__description__ = 'JSON tools'
__status__ = "Internal"


JSON_ENCODING = 'utf-8'
RE_FLAGS = re.MULTILINE | re.DOTALL


###############################################################################
# Errors ######################################################################
###############################################################################
class JSONError(Exception):
    pass


###############################################################################
# Encoders ####################################################################
###############################################################################
class Encoder:
    encoding = None

    def __init__(self, encoding: str):
        self.encoding = encoding

    def encode(self, obj):
        raise NotImplementedError


class BasicEncoder(Encoder):
    BACKSLASH = {'"': '\\"', '\\': '\\\\', '\b': '\\b', '\f': '\\f', '\n': '\\n', '\r': '\\r', '\t': '\\t'}
    escape_re = re.compile(r'[\x00-\x1f\\"\b\f\n\r\t]')
    ITEM_SEPARATOR = ', '
    KEY_SEPARATOR = ': '

    def __init__(self, encoding: str):
        super(BasicEncoder, self).__init__(encoding)

    def encode(self, obj: Any) -> str:
        if isinstance(obj, bytes):
            obj = obj.decode(self.encoding)
        return self.scan(obj)

    def scan(self, obj: Any, throwable: bool=True) -> str:
        if obj is None:
            return 'null'
        elif isinstance(obj, bool):
            return 'true' if obj else 'false'
        elif isinstance(obj, (int, float)):
            return str(obj)
        elif isinstance(obj, str):
            return self.encode_str(obj)
        elif isinstance(obj, list):
            return self.encode_list(obj)
        elif isinstance(obj, dict):
            return self.encode_dict(obj)
        elif throwable:
            raise JSONError('Wrong Python object')

    def encode_str(self, obj: str) -> str:
        _obj = StringIO()
        _obj.write('"')
        _obj.write(self.escape_re.sub(lambda m: self.BACKSLASH[m.group(0)], obj))
        _obj.write('"')
        return _obj.getvalue()

    def encode_list(self, obj: Iterable) -> str:
        if not obj:
            return '[]'
        _obj = StringIO()
        _obj.write('[')
        it = iter(obj)
        _obj.write(self.scan(next(it)))
        for item in it:
            _obj.write(self.ITEM_SEPARATOR)
            _obj.write(self.scan(item))
        _obj.write(']')
        return _obj.getvalue()

    def encode_dict(self, obj: Mapping) -> str:
        if not obj:
            return '{}'
        _obj = StringIO()
        _obj.write('{')
        it = iter(obj)
        key = next(it)
        _obj.write(self.encode_str(key))
        _obj.write(self.KEY_SEPARATOR)
        _obj.write(self.scan(obj[key]))
        for key in it:
            _obj.write(self.ITEM_SEPARATOR)
            _obj.write(self.encode_str(key))
            _obj.write(self.KEY_SEPARATOR)
            _obj.write(self.scan(obj[key]))
        _obj.write('}')
        return _obj.getvalue()


_default_encoder = BasicEncoder(JSON_ENCODING)


class AdvancedEncoder(BasicEncoder):
    def __init__(self, encoding: str=JSON_ENCODING):
        super(AdvancedEncoder, self).__init__(encoding)

    def scan(self, obj: Any, throwable: bool=True) -> str:
        s = super(AdvancedEncoder, self).scan(obj, False)
        if s is not None:
            return s
        elif isinstance(obj, uuid.UUID):
            return ''.join(('"', str(obj), '"'))
        elif isinstance(obj, complex):
            return ''.join(('{"real": ', str(obj.real),
                            ', "imag": ', str(obj.imag), '}'))
        elif isinstance(obj, slice):
            return ''.join(('{"start": ', str(obj.start),
                            ', "stop": ', str(obj.stop),
                            ', "step": ', str(obj.step), '}'))
        elif isinstance(obj, (date, time)):
            return self.encode_datetime(obj)
        elif isinstance(obj, abc.Iterable):
            if isinstance(obj, (abc.Sequence, abc.Set)):
                return self.encode_list(obj)
            elif isinstance(obj, abc.Mapping):
                return self.encode_dict(obj)
        elif throwable:
            raise JSONError('Wrong Python object')

    def encode_datetime(self, obj: Union[date, time]) -> str:
        if isinstance(obj, datetime):
            obj = obj.replace(microsecond=0).astimezone()
        elif isinstance(obj, time):
            obj = obj.replace(microsecond=0)
        obj_iso = obj.isoformat()
        if obj_iso.endswith(('-00:00', '+00:00')):
            obj_iso = obj_iso[0:-6] + 'Z'
        return ''.join(('"', obj_iso, '"'))


class CustomEncoder(AdvancedEncoder):

    def __init__(self, encoding: str=JSON_ENCODING):
        super(CustomEncoder, self).__init__(encoding)

    def scan(self, obj: Any, throwable: bool=True) -> str:
        s = super(CustomEncoder, self).scan(obj, False)
        if s is not None:
            return s
        elif self.is_object(obj):
            return self.encode_object(obj)
        elif throwable:
            raise JSONError('Wrong Python object')

    def is_object(self, obj) -> bool:
        return not (inspect.ismodule(obj) or inspect.isclass(obj) or inspect.isroutine(obj) or inspect.iscode(obj)
                    or inspect.isframe(obj) or inspect.istraceback(obj) or inspect.iscoroutine(obj)
                    or inspect.isgenerator(obj) or inspect.isasyncgen(obj) or inspect.ismemberdescriptor(obj)
                    or inspect.isdatadescriptor(obj) or inspect.isgetsetdescriptor(obj)
                    or inspect.ismethoddescriptor(obj))

    def has_func(self, obj, func) -> bool:
        if not hasattr(obj, func):
            return False
        return inspect.isroutine(getattr(obj, func))

    def encode_object(self, obj: Any) -> str:
        if self.has_func(obj, '__getstate__'):
            data = obj.getstate()
            if data is not False:
                return self.scan(data)
        if self.has_func(obj, '__json__'):
            return obj.__json__()
        if hasattr(obj, '__dict__') or hasattr(obj, '__slots__'):
            if hasattr(obj, '__dict__'):
                data = dict(obj.__dict__)
            elif hasattr(obj, '__slots__'):
                data = dict(obj.__slots__)
            else:
                data = dict()
            for base in inspect.getmro(type(obj)):
                if hasattr(base, '__dict__'):
                    data.update({k: v for k, v in base.__dict__.items() if k not in data})
                elif hasattr(base, '__slots__'):
                    if hasattr(base, base.__slots__[0]):
                        for item in base.__slots__:
                            data[item] = getattr(base, item)
                    else:
                        data[base.__slots__] = getattr(base, base.__slots__)
            return self.scan({k: v for k, v in data.items()
                              if k not in dir(type('', (), {})) and not inspect.isroutine(v)})


###############################################################################
# Decoders ####################################################################
###############################################################################
class Decoder:
    encoding = None

    def __init__(self, encoding: str):
        self.encoding = encoding

    def decode(self, s):
        raise NotImplementedError


class BasicDecoder(Decoder):
    BACKSLASH = {'"': '"', '\\': '\\', '/': '/', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t'}
    utf8_bom_re = re.compile(r"^[\uFEFF]??")
    whitespace_re = re.compile(r'[ \t\n\r]*', RE_FLAGS)
    null_re = re.compile(r'null')
    boolean_re = re.compile(r'true|false')
    number_re = re.compile(r'(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?', RE_FLAGS)
    chunk_str_re = re.compile(r'(.*?)(["\\])', RE_FLAGS)

    def __init__(self, encoding: str):
        super(BasicDecoder, self).__init__(encoding)

    def skip_whitespace(self, s: str, pos: int) -> int:
        return self.whitespace_re.match(s, pos).end()

    def decode(self, s: str) -> Any:
        if not s or not isinstance(s, str):
            raise JSONError('Only "str" type is acceptable')
        pos = self.utf8_bom_re.match(s).end()
        obj, pos = self.scan(s, pos)
        if self.skip_whitespace(s, pos) != len(s):
            raise JSONError('Incorrect end of json string')
        return obj

    def scan(self, s: str, pos: int) -> Tuple[Any, int]:
        pos = self.skip_whitespace(s, pos)
        if s[pos] == 'n':
            return self.decode_null(s, pos)
        elif s[pos] == 't' or s[pos] == 'f':
            return self.decode_boolean(s, pos)
        elif s[pos] in '-0123456789':
            return self.decode_number(s, pos)
        elif s[pos] == '"':
            return self.decode_string(s, pos)
        elif s[pos] == '[':
            return self.decode_array(s, pos)
        elif s[pos] == '{':
            return self.decode_object(s, pos)
        else:
            raise JSONError('Wrong JSON string')

    def decode_null(self, s: str, pos: int) -> Tuple[None, int]:
        m = self.null_re.match(s, pos)
        if m is None:
            raise JSONError('Error in parsing json "null" string')
        return None, m.end()

    def decode_boolean(self, s: str, pos: int) -> Tuple[bool, int]:
        m = self.boolean_re.match(s, pos)
        if m is None:
            raise JSONError('Error in parsing json "boolean" string')
        return m.group() == 'true', m.end()

    def decode_number(self, s: str, pos: int) -> Tuple[Union[int, float], int]:
        m = self.number_re.match(s, pos)
        if m is None:
            raise JSONError('Error in parsing json "number" string')
        i, f, e = m.groups()
        if f or e:
            return float(m.group()), m.end()
        else:
            return int(i), m.end()

    def decode_string(self, s: str, pos: int) -> Tuple[str, int]:
        _string = StringIO()
        end = pos + 1
        while True:
            m = self.chunk_str_re.match(s, end)
            if m is None:
                raise JSONError('Error in parsing json "string" string')
            chunk, term = m.groups()
            if chunk:
                _string.write(chunk)
            end = m.end()
            if term == '"':
                break
            else:
                try:
                    esc = s[end]
                except IndexError:
                    raise JSONError('Error in parsing json "string" string')
                if esc == 'u':
                    char = bytes(s[end - 1: end + 5], 'utf-8').decode('unicode-escape')
                    end += 5
                else:
                    try:
                        char = self.BACKSLASH[esc]
                        end += 1
                    except KeyError:
                        raise JSONError('Error in parsing json "string" string')
                _string.write(char)
        return _string.getvalue(), end

    def decode_array(self, s: str, pos: int) -> Tuple[List[Any], int]:
        _array = list()
        end = self.skip_whitespace(s, pos+1)
        if s[end] == ']':
            return _array, end + 1
        while True:
            value, end = self.scan(s, end)
            _array.append(value)
            end = self.skip_whitespace(s, end)
            if s[end] == ']':
                break
            elif s[end] == ',':
                end += 1
                continue
            else:
                raise JSONError('Error in parsing json "array" string')
        return _array, end + 1

    def decode_object(self, s: str, pos: int) -> Tuple[Dict[str, Any], int]:
        _obj = dict()
        end = self.skip_whitespace(s, pos+1)
        if s[end] == '}':
            return _obj, end + 1
        while True:
            end = self.skip_whitespace(s, end)
            key, end = self.decode_string(s, end)
            end = self.skip_whitespace(s, end)
            if s[end] != ':':
                raise JSONError('Error in parsing json "object" string')
            value, end = self.scan(s, end + 1)
            _obj[key] = value
            end = self.skip_whitespace(s, end)
            if s[end] == '}':
                break
            elif s[end] == ',':
                end += 1
                continue
            else:
                raise JSONError('Error in parsing json "object" string')
        return _obj, end + 1


_default_decoder = BasicDecoder(JSON_ENCODING)


class AdvancedDecoder(BasicDecoder):
    uuid_re = re.compile(r'[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}', re.IGNORECASE)
    date_re = re.compile(r'(?P<year>[12]\d{3})-(?P<month>0[1-9]|1[0-2])-(?P<day>0[1-9]|[12]\d|3[01])')
    time_re = re.compile(r'(?P<hour>2[0-3]|[01][0-9]):(?P<minute>[0-5][0-9])'
                         r'(?::(?P<second>[0-5][0-9])(?:\.(?P<microsecond>[0-9]{1,6})[0-9]{0,6})?)?')
    datetime_re = re.compile(date_re.pattern + r'[T ]' + time_re.pattern +
                             r'(?P<tzinfo>Z|[+-][0-9]{2}(?::?[0-9]{2})?)?')

    def __init__(self, encoding: str=JSON_ENCODING):
        super(AdvancedDecoder, self).__init__(encoding)

    def decode_string(self, s: str, pos: int):
        obj, end = super(AdvancedDecoder, self).decode_string(s, pos)
        m = self.uuid_re.fullmatch(obj)
        if m:
            return uuid.UUID(obj), end
        m = self.datetime_re.fullmatch(obj)
        if m:
            kw = m.groupdict()
            if 'microsecond' in kw and kw['microsecond']:
                kw['microsecond'] = kw['microsecond'].ljust(6, '0')
            tz = kw.pop('tzinfo')
            if tz == 'Z' or tz == 'z':
                tz = timezone.utc
            elif tz is not None:
                offset_mins = int(tz[-2:]) if len(tz) > 3 else 0
                offset = 60 * int(tz[1:3]) + offset_mins
                if tz[0] == '-':
                    offset = -offset
                tz = timezone(timedelta(minutes=offset))
            kw = {k: int(v) for k, v in kw.items() if v is not None}
            kw['tzinfo'] = tz
            return datetime(**kw), end
        m = self.date_re.fullmatch(obj)
        if m:
            return date(**{k: int(v) for k, v in m.groupdict().items()}), end
        m = self.time_re.fullmatch(obj)
        if m:
            kw = m.groupdict()
            if 'microsecond' in kw and kw['microsecond']:
                kw['microsecond'] = kw['microsecond'].ljust(6, '0')
            return time(**{k: int(v) for k, v in kw.items() if v is not None}), end
        return obj, end

    def decode_object(self, s: str, pos: int):
        obj, end = super(AdvancedDecoder, self).decode_object(s, pos)
        if len(obj) == 2 and all(map(lambda x: x in obj, ('real', 'imag'))):
            obj = complex(**{k: v for k, v in obj.items() if v is not None})
        elif len(obj) == 3 and all(map(lambda x: x in obj, ('start', 'stop', 'step'))):
            obj = slice(*[v for v in obj.values() if v is not None])
        return obj, end


class CustomDecoder(AdvancedDecoder):
    
    def __init__(self, encoding: str=JSON_ENCODING):
        super(CustomDecoder, self).__init__(encoding)

    def decode(self, s: str, clazz: type=None) -> Any:
        obj = super(CustomDecoder, self).decode(s)
        if clazz is None:
            return obj
        else:
            return self.customize(obj, clazz)

    def customize(self, obj: Any, clazz: Type):
        values = inspect.signature(clazz.__init__).parameters.values()
        values = list(values)[1:] if len(values) > 1 else None
        if values is None:
            return clazz()
        elif isinstance(obj, (type(None), bool, str, int, float, datetime, date, time, uuid.UUID)):
            if len(values) != 1:
                raise JSONError('Error in casting python object')
            return clazz(obj)
        elif isinstance(obj, (abc.Sequence, abc.Set)):
            if len(values) != len(obj):
                raise JSONError('Error in casting python object')
            return clazz(*obj)
        else:
            if len(values) > len(obj):
                raise JSONError('Error in casting python object')
            keys = list(inspect.signature(clazz.__init__).parameters.keys())[1:]
            _obj = {}
            for key in keys:
                if key in obj:
                    _obj[key] = obj[key]
                else:
                    raise JSONError('Error in casting python object')
            return clazz(**_obj)


###############################################################################
# Formatter ###################################################################
###############################################################################
class Formatter:
    item_sep = None
    key_sep = None
    align = None
    indent = None
    eol = None

    def __init__(self, align: int, indent: int, item_sep: str, key_sep: str, eol: str):
        self.align = align
        self.indent = indent
        self.item_sep = item_sep
        self.key_sep = key_sep
        self.eol = eol

    def format(self, s: str):
        raise NotImplementedError


class DefaultFormatter(Formatter):
    def __init__(self, align: int=0, indent: int=4, item_sep: str=',\r\n', key_sep: str=': ', eol: str='\r\n'):
        super(DefaultFormatter, self).__init__(align, indent, item_sep, key_sep, eol)

    def format(self, s: str):
        if not s or not isinstance(s, str):
            raise JSONError('Only "str" type is acceptable')
        js = StringIO()
        pos = _default_decoder.utf8_bom_re.match(s).end()
        pos = _default_decoder.skip_whitespace(s, pos)
        js.write(s[0: pos])
        obj, pos = self.scan(s, pos, self.align)
        js.write(obj)
        if _default_decoder.skip_whitespace(s, pos) != len(s):
            raise JSONError('Incorrect end of json string')
        js.write(s[pos:])
        return js.getvalue()

    def scan(self, s: str, pos: int, align: int) -> Tuple[str, int]:
        pos = _default_decoder.skip_whitespace(s, pos)
        if s[pos] == 'n':
            return self.format_null(s, pos, align)
        elif s[pos] == 't' or s[pos] == 'f':
            return self.format_boolean(s, pos, align)
        elif s[pos] in '-0123456789':
            return self.format_number(s, pos, align)
        elif s[pos] == '"':
            return self.format_string(s, pos, align)
        elif s[pos] == '[':
            return self.format_array(s, pos, align)
        elif s[pos] == '{':
            return self.format_object(s, pos, align)
        else:
            raise JSONError('Wrong JSON string')

    @staticmethod
    def concat(*s):
        return ''.join(map(lambda x: ' '*x if isinstance(x, int) else x, s))

    def format_null(self, s: str, pos: int, align: int) -> Tuple[str, int]:
        m = _default_decoder.null_re.match(s, pos)
        if m is None:
            raise JSONError('Error in formatting json "null" string')
        return self.concat(align, m.group()), m.end()

    def format_boolean(self, s: str, pos: int, align: int) -> Tuple[str, int]:
        m = _default_decoder.boolean_re.match(s, pos)
        if m is None:
            raise JSONError('Error in formatting json "boolean" string')
        return self.concat(align, m.group()), m.end()

    def format_number(self, s: str, pos: int, align: int) -> Tuple[str, int]:
        m = _default_decoder.number_re.match(s, pos)
        if m is None:
            raise JSONError('Error in formatting json "number" string')
        return self.concat(align, m.group()), m.end()

    def format_string(self, s: str, pos: int, align: int) -> Tuple[str, int]:
        end = pos + 1
        while True:
            m = _default_decoder.chunk_str_re.match(s, end)
            if m is None:
                raise JSONError('Error in formatting json "string" string')
            _, term = m.groups()
            end = m.end()
            if term == '"':
                break
            else:
                end += 5 if s[end] == 'u' else 1
        return self.concat(align, s[pos: end]), end

    def format_array(self, s: str, pos: int, align: int) -> Tuple[str, int]:
        end = _default_decoder.skip_whitespace(s, pos+1)
        if s[end] == ']':
            end += 1
            return self.concat(align, s[pos: end]), end
        js = StringIO()
        js.write(self.concat(align, s[pos], self.eol))
        align += self.indent
        while True:
            value, end = self.scan(s, end, align)
            js.write(value)
            end = _default_decoder.skip_whitespace(s, end)
            if s[end] == ']':
                js.write(self.eol)
                break
            elif s[end] == ',':
                end += 1
                js.write(self.item_sep)
                continue
            else:
                raise JSONError('Error in parsing json "array" string')
        align -= self.indent
        js.write(self.concat(align, ']'))
        return js.getvalue(), end + 1

    def format_object(self, s: str, pos: int, align: int) -> Tuple[str, int]:
        end = _default_decoder.skip_whitespace(s, pos+1)
        if s[end] == '}':
            end += 1
            return self.concat(align, s[pos: end]), end
        js = StringIO()
        js.write(self.concat(align, s[pos], self.eol))
        align += self.indent
        while True:
            end = _default_decoder.skip_whitespace(s, end)
            key, end = self.format_string(s, end, align)
            end = _default_decoder.skip_whitespace(s, end)
            if s[end] != ':':
                raise JSONError('Error in parsing json "object" string')
            js.write(self.concat(key, self.key_sep))
            value, end = self.scan(s, end + 1, align)
            js.write(value.lstrip())
            end = _default_decoder.skip_whitespace(s, end)
            if s[end] == '}':
                js.write(self.eol)
                break
            elif s[end] == ',':
                end += 1
                js.write(self.item_sep)
                continue
            else:
                raise JSONError('Error in parsing json "object" string')
        align -= self.indent
        js.write(self.concat(align, '}'))
        return js.getvalue(), end + 1


_default_formatter = DefaultFormatter()


###############################################################################
# APIs ########################################################################
###############################################################################
def formats(s: str, align: int=0, indent: int=4, item_sep: str=',\r\n', key_sep: str=': ', eol: str='\r\n') -> str:
    if align == 0 and indent == 4 and item_sep == ',\r\n' and key_sep == ': ' and eol == '\r\n':
        return _default_formatter.format(s)
    return DefaultFormatter(align=align, indent=indent, item_sep=item_sep, key_sep=key_sep, eol=eol).format(s)


def dumps(obj: Any, encoding: str=JSON_ENCODING, cls: Type[Encoder]=CustomEncoder, indent: int=None) -> str:
    _encoder = _default_encoder if encoding == JSON_ENCODING and cls is BasicEncoder else cls(encoding)
    js = _encoder.encode(obj)
    if indent is not None:
        return formats(js)
    return js


def dump(obj: Any, fp: TextIO, encoding: str=JSON_ENCODING, cls: Type[Encoder]=CustomEncoder, indent: int=None):
    fp.write(dumps(obj=obj, encoding=encoding, cls=cls, indent=indent))


def loads(s: str, encoding: str=JSON_ENCODING, cls: Type[Decoder]=CustomDecoder, clazz: type=None) -> Any:
    if isinstance(s, bytes):
        s = s.decode(encoding)
    if clazz is None:
        if encoding == JSON_ENCODING and cls is BasicDecoder:
            return _default_decoder.decode(s)
        else:
            return cls(encoding).decode(s)
    else:
        return CustomDecoder(encoding).decode(s, clazz)


def load(fp: TextIO, encoding: str=JSON_ENCODING, cls: Type[Decoder]=CustomDecoder, clazz: type=None) -> Any:
    return loads(fp.read(), encoding=encoding, cls=cls, clazz=clazz)
