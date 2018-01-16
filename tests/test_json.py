#!/usr/bin/env python
# coding: utf-8

import timeit
import uuid
from collections import deque
from datetime import timedelta, timezone
from datetime import datetime
from collections import UserList, UserDict
from unittest import TestCase
import jsonease as sj


class Student(object):
    name = None
    score = None
    pass_line = 60
    passed = False

    def __init__(self, name='sljf', passed=False):
        self.name = name
        self.score = 0
        self.passed = passed

    def set_score(self, score):
        self.score = score
        self.passed = self.score > 60

    def is_passed(self):
        return self.passed

    def encourage(self):
        print('encourage ' + self.name)

    @classmethod
    def hello(cls):
        print('hello' + cls.pass_line)

    @staticmethod
    def set_pass_line(pass_line):
        Student.pass_line = pass_line


class TestJson(TestCase):

    def test_loads_null(self):
        samples = ['null', 'null   ', '   null', '    null    ']
        for s in samples:
            self.assertEqual(None, sj.loads(s))

        samples = ['nullsdkflsdf', 'djlfsdlnull', 'dskfjlnulllskjflkds']
        for s in samples:
            self.assertRaises(sj.JSONError, sj.loads, s)

    def test_loads_perf_null(self):
        stmt1 = """json.loads('   null   ')"""
        setup1 = "import jsonease as json"
        setup2 = "import json"
        print(timeit.timeit(stmt=stmt1, setup=setup1, number=1000))
        print(timeit.timeit(stmt=stmt1, setup=setup2, number=1000))

    def test_loads_boolean(self):
        samples = ['true', 'false', '   true', '   true   ', 'true   ', '  false', '   false   ', 'false ']
        for s in samples:
            self.assertEqual(bool, type(sj.loads(s)))

        samples = ('truefalse', 'true false', '   true  false ', '  False')
        for s in samples:
            self.assertRaises(sj.JSONError, sj.loads, s)

    def test_loads_perf_boolean(self):
        stmt1 = """json.loads('   true   ')"""
        setup1 = "import jsonease as json"
        setup2 = "import json"
        print(timeit.timeit(stmt=stmt1, setup=setup1, number=1000))
        print(timeit.timeit(stmt=stmt1, setup=setup2, number=1000))

    def test_loads_number(self):
        samples = ['123', '-345', '  234  ', '  -838', '9123   ', '-93290   ', '   1920   ']
        for s in samples:
            self.assertEqual(int, type(sj.loads(s)))

        samples = ['0.23', '-3.45', '  23.4  ', '  -83.8', '912.3   ', '-93.290   ', '   192.0   ']
        for s in samples:
            self.assertEqual(float, type(sj.loads(s)))

        samples = ['--0.123', '.123', '  ..123  ', '-.123 ']
        for s in samples:
            self.assertRaises(sj.JSONError, sj.loads, s)

    def test_loads_perf_number(self):
        stmt1 = """json.loads('  -3.45  ')"""
        setup1 = "import jsonease as json"
        setup2 = "import json"
        print(timeit.timeit(stmt=stmt1, setup=setup1, number=1000))
        print(timeit.timeit(stmt=stmt1, setup=setup2, number=1000))

    def test_loads_string(self):
        sample = ' "l  sk \\n jfds"  '
        print(sj.loads(sample))

    def test_loads_perf_string_1(self):
        samples = ('  "  dslddjjjjjjjjj\\u7890jjjjjjjjjjjjjjjs"', )
        for s in samples:
            start_time_1 = datetime.now()
            print(sj.loads(s))
            print(datetime.now()-start_time_1)
            start_time_2 = datetime.now()
            #print(js.loads(s))
            print(datetime.now()-start_time_2)

    def test_loads_perf_string_2(self):
        stmt1 = """json.loads('  "  dslddjjjjjjjjj\\u7890jjjjjjjjjjjjjjjs"')"""
        setup1 = "import jsonease as json"
        setup2 = "import json"
        print(timeit.timeit(stmt=stmt1, setup=setup1, number=1000))
        print(timeit.timeit(stmt=stmt1, setup=setup2, number=1000))

    def test_loads_array(self):
        sample = '[[[[[[]]]]],[],[],[],[]     ]'
        self.assertEqual(list, type(sj.loads(sample)))
        sample = '[ null , false , ["ldskfjls", null, [], [[]]],  true, "  dslddjjjjjjjjj\\u7890jjjjjjjjjjjjjjjs"  , 123, -12312, -0.111 ]   '
        self.assertEqual(list, type(sj.loads(sample)))

    def test_loads_object(self):
        sample = '  { "haha": 123, "dslkjf": false, "yifan": true, "h\\naha1": null , "haha3": [[[[[[null]]]]],[],[],[],[]     ], "haha4:": {"haha":{"haha":{"haha2:":[null, true, -0.334, "haha"]}}}}   '
        self.assertEqual(dict, type(sj.loads(sample)))

    def test_dumps_null(self):
        sample = None
        self.assertEqual('null', sj.dumps(sample))

    def test_dumps_bool(self):
        samples = {'true': True, 'false': False}
        for k, v in samples.items():
            self.assertEqual(k, sj.dumps(v))

    def test_dumps_number(self):
        samples = {'123': 123, '-123': -123, '0.123': 0.123, '0': 0}
        for k, v in samples.items():
            self.assertEqual(k, sj.dumps(v))

    def test_dumps_string(self):
        sample = {'"123"': '123', '"123\\n456"': '123\n456'}
        for k, v in sample.items():
            self.assertEqual(k, sj.dumps(v))

    def test_dumps_list(self):
        samples = {'[]': [], '["abc", true]': ['abc', True]}
        for k, v in samples.items():
            self.assertEqual(k, sj.dumps(v))

    def test_dumps_dict(self):
        samples = {'{}': {}, '{"abc": true}': {"abc": True}, '{"def": [false]}': {"def": [False]}}
        for k, v in samples.items():
            self.assertEqual(k, sj.dumps(v))

    def test_dumps_indented(self):
        sample0 = {"def": [False, {'haha': 123, "toto": [123, 45, None, [False, True]]}], '123': None, '4334': []}
        sample1 = [False, {'haha': 123, "toto": [123, 45, None, [False, True]]}]
        sample2 = [False, {'haha': 123, 'toto': [False, {'nini': 'xixi'}]}, True]
        sample3 = {'n1': False, 'n2': {'n3': None, 'n4': True}, 'nn': 'tsdf'}
        sample4 = [{}, {}]
        sample5 = [False, {'haha': 123, 'toto': [False, {'nini': 'xixi', 'lala': [False, {'haha': 123, "toto": [123, 45, None, [False, True]]}]}]}, True]

        self.assertEqual('{\r\n    "def": [\r\n        false,\r\n        {\r\n            "haha": 123,\r\n            '
                         '"toto": [\r\n                123,\r\n                45,\r\n                null,\r\n        '
                         '        [\r\n                    false,\r\n                    true\r\n                ]\r\n '
                         '           ]\r\n        }\r\n    ],\r\n    "123": null,\r\n    '
                         '"4334": []\r\n}', sj.dumps(sample0, indent=4))
        self.assertEqual('[\r\n    false,\r\n    {\r\n        "haha": 123,\r\n        "toto": [\r\n            123,\r\n'
                         '            45,\r\n            null,\r\n            [\r\n                false,\r\n          '
                         '      true\r\n            ]\r\n        ]\r\n    }\r\n]', sj.dumps(sample1, indent=4))
        self.assertEqual('[\r\n    false,\r\n    {\r\n        "haha": 123,\r\n        "toto": [\r\n            '
                         'false,\r\n            {\r\n                "nini": "xixi"\r\n            }\r\n        ]\r\n  '
                         '  },\r\n    true\r\n]', sj.dumps(sample2, indent=4))
        self.assertEqual('{\r\n    "n1": false,\r\n    "n2": {\r\n        "n3": null,\r\n        "n4": true\r\n   '
                         ' },\r\n    "nn": "tsdf"\r\n}', sj.dumps(sample3, indent=4))
        self.assertEqual('[\r\n    {},\r\n    {}\r\n]', sj.dumps(sample4, indent=4))

        self.assertEqual('[\r\n    false,\r\n    {\r\n        "haha": 123,\r\n        "toto": [\r\n           '
                         ' false,\r\n            {\r\n                "nini": "xixi",\r\n                "lala": [\r\n'
                         '                    false,\r\n                    {\r\n                       '
                         ' "haha": 123,\r\n                        "toto": [\r\n                            123,\r\n   '
                         '                         45,\r\n                            null,\r\n                        '
                         '    [\r\n                                false,\r\n                                true\r\n  '
                         '                          ]\r\n                        ]\r\n                    }\r\n        '
                         '        ]\r\n            }\r\n        ]\r\n    },\r\n    true\r\n]',
                         sj.dumps(sample5, indent=4))

    def test_advanced_dumps(self):
        sample = UserList([False, 123, UserDict({}), 5+5j, UserDict({'haha': 2+3j, 'toto': [False, {'nini': 'xixi'}]}), True])
        self.assertEqual('[\r\n    false,\r\n    123,\r\n    {},\r\n    {\r\n        "real": 5.0,\r\n       '
                         ' "imag": 5.0\r\n    },\r\n    {\r\n        "haha": {\r\n            "real": 2.0,\r\n       '
                         '     "imag": 3.0\r\n        },\r\n        "toto": [\r\n            false,\r\n           '
                         ' {\r\n                "nini": "xixi"\r\n            }\r\n        ]\r\n    },\r\n  '
                         '  true\r\n]', sj.dumps(sample, cls=sj.AdvancedEncoder, indent=4))

        sample = UserList([False, datetime.now().date(), 123, UserDict({}), 5+5j, UserDict({'haha': 2+3j, 'toto': [False, {'nini': 'xixi'}]}), True])
        haha=sj.dumps(sample, cls=sj.AdvancedEncoder, indent=4)
        print(haha)
        hhh = sj.loads(haha, cls=sj.AdvancedDecoder)
        print(hhh)

    def test_advanced_complex(self):
        sample = UserList([False, 123, UserDict({}), 5+5j, UserDict({'haha': 2+3j, 'toto': [False, {'nini': 'xixi'}]}), True])
        output1 = sj.dumps(sample, cls=sj.AdvancedEncoder, indent=2)
        sample = deque([False, 123, UserDict({}), 5+5j, UserDict({'haha': 2+3j, 'toto': [False, {'nini': 'xixi'}]}), True])
        output2 = sj.dumps(sample, cls=sj.AdvancedEncoder, indent=2)
        self.assertEqual(output1, output2)
        output3 = sj.loads(output1, cls=sj.AdvancedDecoder)
        print(output3)
        self.assertEqual([False, 123, {}, (5+5j), {'haha': (2+3j), 'toto': [False, {'nini': 'xixi'}]}, True], output3)
        self.assertTrue(isinstance(output3[3], complex))

    def test_advanced_datetime(self):
        dt = datetime(year=2017, month=11, day=20, hour=10, minute=53, second=22, tzinfo=timezone(timedelta(-1, 68400)))
        b = UserDict({'haha': 2+3j, 'toto': [False, dt]})
        c = sj.dumps(b, cls=sj.AdvancedEncoder)
        self.assertEqual('{"haha": {"real": 2.0, "imag": 3.0}, "toto": [false, "2017-11-20T10:53:22-05:00"]}', c)
        print(c)
        d = sj.loads(c, cls=sj.AdvancedDecoder)
        self.assertEqual({'haha': (2+3j), 'toto': [False, datetime(2017, 11, 20, 10, 53, 22, tzinfo=timezone(timedelta(-1, 68400)))]}, d)
        print(d)

    def test_advanced_uuid(self):
        _uuid = uuid.uuid1()
        sample = deque([False, _uuid, 123, UserDict({}), 5+5j, UserDict({'haha': 2+3j, 'toto': [False, {'nini': 'xixi'}]}), True])
        output = sj.dumps(sample, cls=sj.AdvancedEncoder)
        print(output)
        self.assertEqual('[false, "%s", 123, {}, {"real": 5.0, "imag": 5.0}, {"haha": {"real": 2.0, "imag": 3.0}, "toto": [false, {"nini": "xixi"}]}, true]' % _uuid, output)
        output2 = sj.loads(output, cls=sj.AdvancedDecoder)
        print(output2)
        self.assertEqual([False, _uuid, 123, {}, (5+5j), {'haha': (2+3j), 'toto': [False, {'nini': 'xixi'}]}, True], output2)

    def test_advanced_slice(self):
        _slice = slice(1, 5, 2)
        sample = deque([False, _slice, 123, UserDict({}), 5+5j, UserDict({'haha': 2+3j, 'toto': [False, {'nini': 'xixi'}]}), True])
        output = sj.dumps(sample, cls=sj.AdvancedEncoder)
        print(output)
        self.assertEqual('[false, {"start": 1, "stop": 5, "step": 2}, 123, {}, {"real": 5.0, "imag": 5.0}, {"haha": {"real": 2.0, "imag": 3.0}, "toto": [false, {"nini": "xixi"}]}, true]', output)
        output2 = sj.loads(output, cls=sj.AdvancedDecoder)
        print(output2)
        self.assertEqual([False, _slice, 123, {}, (5+5j), {'haha': (2+3j), 'toto': [False, {'nini': 'xixi'}]}, True], output2)

    def test_custom(self):
        toto = Student('toto')
        self.assertTrue(isinstance(toto, Student))
        a = sj.dumps(toto)
        py_a = sj.loads(a, clazz=Student)
        a2 = sj.dumps(py_a)
        self.assertEqual(a, a2)