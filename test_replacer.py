#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import unittest
from unittest import mock
import tempfile


class Weechat(object):
    """Mock weechat interface"""
    ACTION = '*'
    ERROR = '=!='
    NETWORK = '--'
    JOIN = '-->'
    QUIT = '<--'
    WEECHAT_RC_OK = 0
    WEECHAT_LIST_POS_SORT = 1

    def __init__(self):
        self.wbuffer = ''
        self.completions = []
        self.position = 0
        self.line = ''

    def register(self, *args, **kwargs):
        pass

    def color(self, color):
        return color

    def prnt(self, we_buff, msg):
        self.wbuffer = msg

    def prefix(self, arg):
        _map = {'action': Weechat.ACTION,
                'error': Weechat.ERROR,
                'network': Weechat.NETWORK,
                'join': Weechat.JOIN,
                'quit': Weechat.QUIT}
        return _map[arg]

    def hook_completion(self, *args, **kwargs):
        pass

    def hook_command(self, *args, **kwargs):
        pass

    def hook_completion_list_add(self, completion, item, index, sort):
        self.completions.append(item)

    def buffer_get_integer(self, *args, **kwargs):
        return self.position

    def buffer_get_string(self, *args, **kwargs):
        return self.line

    def buffer_set(self, wbuffer, what, value):
        _map = {'input': self._set_line,
                'input_pos': self._set_position}
        _map[what](value)

    def _set_line(self, val):
        self.line = val

    def _set_position(self, val):
        self.position = val

    def string_eval_path_home(self, path, pointers, extra_vars, options):
        return path

    def info_get(self, key, args):
        _map = {'weechat_data_dir': None,
                'weechat_config_dir': None,
                'version_number': 0x3020000}
        return _map.get(key)


weechat = Weechat()
sys.modules['weechat'] = weechat


import replacer


class TestReplacer(unittest.TestCase):

    @mock.patch('replacer.Replacer._locate_replacement_file')
    def setUp(self, rfile):
        fd, fname = tempfile.mkstemp()
        os.close(fd)
        rfile.return_value = fname
        self._path = fname
        self.repl = replacer.Replacer()

    def tearDown(self):
        self.repl = None
        try:
            os.unlink(self._path)
        except OSError:
            pass

    def test_init(self):
        self.assertDictEqual(self.repl.replacement_map, {})

    def test_add(self):
        self.repl.add('foo', 'bar')
        self.assertDictEqual(self.repl.replacement_map, {'foo': 'bar'})

    def test_delete(self):
        self.repl.add('foo', 'bar')
        self.assertFalse(self.repl.delete('baz'))
        self.assertTrue(self.repl.delete('foo'))
        self.assertDictEqual(self.repl.replacement_map, {})


class TestDummyTests(unittest.TestCase):
    """
    This, somehow stupid test ensures, that process of reading default
    replacer config file works
    """
    def tearDown(self):
        replacer.Replacer.self_object = None

    @mock.patch('replacer.Replacer._locate_replacement_file')
    def test_init(self, rfile):
        rfile.return_value = 'dummy_path'
        repl = replacer.Replacer()
        self.assertIsInstance(repl.replacement_map, dict)

    @mock.patch('replacer.Replacer._locate_replacement_file')
    def test_main(self, rfile):
        rfile.return_value = 'dummy_path'
        replacer.Replacer.self_object = replacer.Replacer()
        replacer.main()

    @mock.patch('replacer.Replacer._locate_replacement_file')
    def test_injector(self, rfile):

        rfile.return_value = 'dummy_path'

        def fun(first, *args, **kwargs):
            return first

        self.assertIsNone(replacer.Replacer.self_object)
        robj = replacer.inject_replacer_object(fun)()
        self.assertIsNotNone(replacer.Replacer.self_object)
        self.assertIsInstance(robj, replacer.Replacer)


class TestFunctions(unittest.TestCase):

    @mock.patch('replacer.Replacer._locate_replacement_file')
    def setUp(self, rfile):
        fd, fname = tempfile.mkstemp()
        os.close(fd)
        self._path = fname
        rfile.return_value = fname
        replacer.Replacer.self_object = replacer.Replacer()
        self.rc = replacer.Replacer

    def tearDown(self):
        self.rc.self_object = None
        try:
            os.unlink(self._path)
        except OSError:
            pass
        weechat.completions = []

    def test_echo(self):
        replacer.echo('a', None)
        self.assertEqual(weechat.wbuffer, 'a')

        replacer.echo('a', None, 'action')
        self.assertEqual(weechat.wbuffer, '%sa' % Weechat.ACTION)
        replacer.echo('something', None, 'network')
        self.assertEqual(weechat.wbuffer, '%ssomething' % Weechat.NETWORK)

    def test_replace_cmd(self):
        replacer.replace_cmd(None, None, None)
        self.assertIn(Weechat.ERROR, weechat.wbuffer)
        self.assertIn('No replacements defined', weechat.wbuffer)

        self.rc.self_object.replacement_map = {'foo': 'bar'}

        replacer.replace_cmd(None, None, None)
        self.assertEqual(weechat.wbuffer, 'foo chat_delimiters->reset bar')

        args = 'foo bar bazz'
        replacer.replace_cmd(None, None, args)
        self.assertIn(Weechat.ERROR, weechat.wbuffer)
        self.assertIn('Error in command', weechat.wbuffer)

        args = 'add baz bazz'
        replacer.replace_cmd(None, None, args)
        self.assertEqual(weechat.wbuffer,
                         '--added: baz chat_delimiters->reset bazz')
        self.assertDictEqual(self.rc.self_object.replacement_map,
                             {'foo': 'bar', 'baz': 'bazz'})

        args = 'del baz'
        replacer.replace_cmd(None, None, args)
        self.assertEqual(weechat.wbuffer, '--Successfully removed key: baz')

        args = 'del baz'
        replacer.replace_cmd(None, None, args)
        self.assertIn(Weechat.ERROR, weechat.wbuffer)
        self.assertIn('No such keyword', weechat.wbuffer)

    def test_completion_cb(self):
        replacer.completion_cb(None, None, None, None)

        self.rc.self_object.replacement_map = {'foo': 'bar'}

        replacer.completion_cb(None, None, None, None)
        self.assertEqual(weechat.completions, ['foo'])

    def test_replace_cb(self):
        replacer.replace_cb(None, None, None, None)
        self.assertEqual(weechat.position, 0)
        self.assertEqual(weechat.line, '')

        self.rc.self_object.replacement_map = {'foo': 'Vestibulum ante'}

        # quis foo cursus
        #        ^
        weechat.line = 'quis foo cursus'
        weechat.position = 8
        replacer.replace_cb(None, None, None, None)
        self.assertEqual(weechat.line, 'quis Vestibulum ante cursus')

        # quis cursus foo
        #               ^
        weechat.line = 'quis cursus foo'
        weechat.position = 15
        replacer.replace_cb(None, None, None, None)
        self.assertEqual(weechat.line, 'quis cursus Vestibulum ante ')

        # foo quis cursus
        #   ^
        weechat.line = 'foo quis cursus'
        weechat.position = 3
        replacer.replace_cb(None, None, None, None)
        self.assertEqual(weechat.line, 'Vestibulum ante quis cursus')

        # quis cursus
        #     ^
        weechat.line = 'quis cursus'
        weechat.position = 5
        replacer.replace_cb(None, None, None, None)
        self.assertEqual(weechat.line, 'quis cursus')


class TestLocateWeeHome(unittest.TestCase):

    @mock.patch('os.path.exists')
    @mock.patch('weechat.string_eval_path_home')
    @mock.patch('weechat.info_get')
    def test_locate_replacement_file_data_dir(self, info_get, eval_path_home,
                                              path_exists):
        info_get.side_effect = ('foo', 'bar')
        eval_path_home.side_effect = ('baz', )
        path_exists.side_effect = (True, )

        result = replacer.Replacer._locate_replacement_file(object)

        self.assertEqual(result, 'foo/replacement_map.json')

    @mock.patch('os.path.exists')
    @mock.patch('weechat.string_eval_path_home')
    @mock.patch('weechat.info_get')
    def test_locate_replacement_file_config_dir(self, info_get, eval_path_home,
                                                path_exists):
        info_get.side_effect = ('foo', 'bar')
        eval_path_home.side_effect = ('baz', )
        path_exists.side_effect = (False, True)

        result = replacer.Replacer._locate_replacement_file(object)

        self.assertEqual(result, 'bar/replacement_map.json')

    @mock.patch('os.path.exists')
    @mock.patch('weechat.string_eval_path_home')
    @mock.patch('weechat.info_get')
    def test_locate_replacement_file_old_home(self, info_get, eval_path_home,
                                              path_exists):
        info_get.side_effect = ('foo', 'bar')
        eval_path_home.side_effect = ('baz', )
        path_exists.side_effect = (False, False, True)

        result = replacer.Replacer._locate_replacement_file(object)

        self.assertEqual(result, 'baz/replacement_map.json')

    @mock.patch('os.path.exists')
    @mock.patch('weechat.string_eval_path_home')
    @mock.patch('weechat.info_get')
    def test_locate_replacement_default_home_31(self, info_get, eval_path_home,
                                                path_exists):
        info_get.side_effect = ('foo', 'bar', 0x3010000)
        eval_path_home.side_effect = ('baz', 'old/replacement_map.json')
        path_exists.side_effect = (False, False, False)

        result = replacer.Replacer._locate_replacement_file(object)

        self.assertEqual(result, 'old/replacement_map.json')

    @mock.patch('os.path.exists')
    @mock.patch('weechat.string_eval_path_home')
    @mock.patch('weechat.info_get')
    def test_locate_replacement_default_home_32(self, info_get, eval_path_home,
                                                path_exists):
        info_get.side_effect = ('foo', 'bar', 0x3020000, 'new')
        eval_path_home.side_effect = ('baz', )
        path_exists.side_effect = (False, False, False)

        result = replacer.Replacer._locate_replacement_file(object)

        self.assertEqual(result, 'new/replacement_map.json')


if __name__ == '__main__':
    unittest.main()
