# -*- coding: utf-8 -*-
"""
Simple replacer for substitution one keyword with some text using completion
mechanism from weechat.

add: add new replacement to table
del: remove key from table

Without any argument list of defined substitution will be displayed.

Script will replace any defined keyword with the text using tab completion. To
make this work, weechat.completion.default_template should be modified:

/set weechat.completion.default_template "%%(nicks)|%%(irc_channels)|%%(replacer_plugin)"

Examples:
/%(command)s add foo foobar
/%(command)s add testutf ½°C
/%(command)s del testutf
"""

import os
import json

import weechat


NAME = 'replacer'
AUTHOR = 'Roman Dobosz <gryf73@gmail.com>'
VERSION = '1.3'
LICENSE = 'Apache 2'
DESC = 'Word replacer for WeeChat'
COMMAND = 'replacer'

COLOR_DELIMITERS = weechat.color('chat_delimiters')
COLOR_NICK = weechat.color('chat_nick')
COLOR_RESET = weechat.color('reset')


def _decode(string):
    try:
        return string.decode('utf-8')
    except AttributeError:
        return string


def _encode(string):
    try:
        # Encode only, if we have decode attribute, which is available for
        # string only on python2
        string.decode
        return string.encode('utf-8')
    except AttributeError:
        return string


class Replacer(object):
    """Replacer"""

    # This will keep reference to created Replacer object. We need it only
    # one, so it also could be global, but globals are bad, mkay?
    self_object = None

    def __init__(self):
        """Initialize plugin"""
        self.replacement_map = {}
        self._path = self._locate_replacement_file()
        self._get_replacement_map()

    def _locate_replacement_file(self):
        map_file = "replacement_map.json"
        data_dirs = (weechat.info_get("weechat_data_dir", ""),
                     weechat.info_get("weechat_config_dir", ""),
                     weechat.string_eval_path_home("%h", {}, {}, {}))

        for path in data_dirs:
            if os.path.exists(os.path.join(path, map_file)):
                return os.path.join(path, map_file)

        # nothing found. so there is no replacement file. let's assume the
        # right file path.
        version = weechat.info_get("version_number", "") or 0
        if version < 0x3020000:  # < 3.2.0
            path = '%h/' + map_file
            return weechat.string_eval_path_home(path, {}, {}, {})
        else:
            return os.path.join(weechat.info_get("weechat_data_dir", ""),
                                map_file)

    def _get_replacement_map(self):
        """Read json file, and assign it to the replacement_map attr"""
        try:
            with open(self._path) as fobj:
                self.replacement_map = json.load(fobj)
        except (IOError, ValueError):
            pass

    def add(self, key, value):
        """Add item to dict"""
        self.replacement_map[key] = value
        self._write_replacement_map()

    def delete(self, key):
        """remove item from dict"""
        try:
            del self.replacement_map[key]
        except KeyError:
            return False

        self._write_replacement_map()
        return True

    def _write_replacement_map(self):
        """Write replacement table to json file"""
        with open(self._path, "w") as fobj:
            json.dump(self.replacement_map, fobj)


def echo(msg, weechat_buffer, prefix=False, **kwargs):
    """
    Print preformated message. Note, that msg and arguments should be str not
    unicode.
    """
    display_msg = msg

    arg_dict = {'color_delimiters': COLOR_DELIMITERS,
                'color_nick': COLOR_NICK,
                'name': NAME,
                'color_reset': COLOR_RESET}

    if prefix:
        display_msg = "%(symbol)s" + display_msg
        arg_dict['symbol'] = weechat.prefix(prefix)

    arg_dict.update(kwargs)
    weechat.prnt(weechat_buffer, display_msg % arg_dict)


def inject_replacer_object(fun):
    """
    Decorator for injecting replacer object into weechat callback functions,
    since weechat doesn't support assignment of object method
    """
    def wrapper(*args, **kwargs):
        """Wrapper"""
        if not Replacer.self_object:
            Replacer.self_object = Replacer()
        return fun(Replacer.self_object, *args, **kwargs)
    return wrapper


@inject_replacer_object
def replace_cmd(replacer_obj, _, weechat_buffer, args):
    """/replacer command implementation"""
    if not args:
        if not replacer_obj.replacement_map:
            echo("No replacements defined", weechat_buffer, 'error')
        else:
            echo("Defined replacements:", weechat_buffer, 'network')

        for key, value in sorted(replacer_obj.replacement_map.items()):

            echo('%(key)s %(color_delimiters)s->%(color_reset)s %(val)s',
                 weechat_buffer, key=_encode(key), val=_encode(value))

        return weechat.WEECHAT_RC_OK

    cmd = args.split(' ')[0]

    if cmd not in ('add', 'del'):
        echo('Error in command /%(command)s %(args)s (help on command: /help '
             '%(command)s)', weechat_buffer, 'error', args=args,
             command=COMMAND)
        return weechat.WEECHAT_RC_OK

    if cmd == 'add':
        key = args.split(' ')[1].strip()
        value = ' '.join(args.split(' ')[2:]).strip()
        replacer_obj.add(_decode(key), _decode(value))
        echo('added: %(key)s %(color_delimiters)s->%(color_reset)s %(val)s',
             weechat_buffer, 'network', key=key, val=value)

    if cmd == 'del':
        key = ' '.join(args.split(' ')[1:]).strip()
        if not replacer_obj.delete(_decode(key)):
            echo('No such keyword in replacement table: %(key)s',
                 weechat_buffer, 'error', key=key)
        else:
            echo('Successfully removed key: %(key)s', weechat_buffer,
                 'network', key=_encode(key))

    return weechat.WEECHAT_RC_OK


@inject_replacer_object
def completion_cb(replacer_obj, data, completion_item, weechat_buffer,
                  completion):
    """Complete keys from replacement table for add/del command"""
    for key in replacer_obj.replacement_map:
        weechat.hook_completion_list_add(completion, _encode(key), 0,
                                         weechat.WEECHAT_LIST_POS_SORT)
    return weechat.WEECHAT_RC_OK


@inject_replacer_object
def replace_cb(replacer_obj, data, completion_item, weechat_buffer,
               completion):
    """replace keyword with value from replacement table, if found"""
    position = weechat.buffer_get_integer(weechat_buffer, 'input_pos')

    input_line = weechat.buffer_get_string(weechat_buffer, 'input')
    input_line = _decode(input_line)

    if len(input_line) == 0:
        return weechat.WEECHAT_RC_OK

    if input_line[position - 1] == ' ':
        return weechat.WEECHAT_RC_OK

    if position > 0:
        left_space_index = input_line.rfind(' ', 0, position - 1)
        if left_space_index == -1:
            left_space_index = 0
        word = input_line[left_space_index:position].strip()

        if word in replacer_obj.replacement_map:

            replacement = replacer_obj.replacement_map[word]
            if position >= len(input_line.strip()):
                replacement += ' '

            new_line = u''
            if left_space_index:
                new_line += input_line[:left_space_index] + u' '
            new_line += replacement
            new_position = len(new_line)
            new_line += input_line[position:]

            weechat.buffer_set(weechat_buffer, 'input', _encode(new_line))
            weechat.buffer_set(weechat_buffer, 'input_pos', str(new_position))

    return weechat.WEECHAT_RC_OK


def main():
    """Main entry"""

    weechat.register(NAME, AUTHOR, VERSION, LICENSE, DESC, '', '')
    weechat.hook_completion('replacer_plugin', 'Try to match last word with '
                            'those in replacement map keys, and replace it '
                            'with value.', 'replace_cb', '')
    weechat.hook_completion('completion_cb', 'Complete replacement map keys',
                            'completion_cb', '')

    weechat.hook_command(COMMAND, DESC, "[add <word> <text>|del <word>]",
                         __doc__ % {"command": COMMAND},
                         'add|del %(completion_cb)', 'replace_cmd', '')


if __name__ == "__main__":
    main()
