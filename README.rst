weechat-replacer
================

WeeChat plugin for replacing user defined keywords with specified text.

Installation and configuration
------------------------------

In order to use it, you have to have WeeChat with Python plugin support
compiled in. Than, copy ``replacer.py`` to ``~/.local/share/weechat/python/``.
It should run on any version of the Python3.

You can optionally create symbolic link to this script:

.. code:: shell-session

   ln -s ~/.local/share/weechat/python/replacer.py ~/.local/share/weechat/python/autoload/replacer.py

Next, you need to add this *replacer_plugin* to Weechat completion template, so
it'll looks similar to:

.. code::

   /set weechat.completion.default_template "%(nicks)|%(irc_channels)|%(replacer_plugin)"

Next, load the plugin (if you choose to not load it automatically):

.. code::

   /python load replacer.py

Now you all set.

Note, that even though there is possibility for keeping all files in different
place than XDG paths, this case is not tested anymore, and all the issues
regarding old files placement will be ignored.


Usage
-----

Abbreviations will be stored as json file
``$XDG_DATA_HOME/weechat/replacement_map.json``, which usually be
``~/.local/share/weechat/replacement_map.json`` which role is to simply persist
dictionary object on the filesystem. To add some replacement words, and text
which would those words replaced with:

.. code::

   /replacer add foo bar

and than, when you type ``foo`` word and press ``tab`` key, you should get
``bar`` word instead.


License
-------

This plugin is on Apache 2 license. See LICENSE for details.
