#!/usr/bin/env python
# coding: utf-8

import unittest


def test():
    from . import test_json

    suite = unittest.TestSuite()

    suite.addTest(unittest.TestLoader().loadTestsFromModule(test_json))

    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    test()