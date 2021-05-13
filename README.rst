weechat-replacer
================

WeeChat plugin for replacing user defined keywords with specified text.

Installation and configuration
------------------------------

In order to use it, you have to have WeeChat with Python plugin support
compiled in. Than, copy ``replacer.py`` to ``~/.weechat/python/``. You can use
any of the Python version - both Python2 and Python3 are supported. You can
optionally create symbolic link to this script:

.. code:: shell-session

   ln -s ~/.weechat/python/replacer.py ~/.weechat/python/autoload/replacer.py

Next, you need to add this *replacer_plugin* to Weechat completion template, so
it'll looks similar to:

.. code::

   /set weechat.completion.default_template "%(nicks)|%(irc_channels)|%(replacer_plugin)"

Next, load the plugin (if you choose to not load it automatically):

.. code::

   /python load replacer.py

Now you all set.


Usage
-----

Abbreviations will be stored as json file ``~/.weechat/replacement_map.json``,
which role is to simply persist dictionary object on the filesystem. To add
some replacement words, and text which would those words replaced with:

.. code::

   /replacer add foo bar

and than, when you type ``foo`` word and press ``tab`` key, you should get
``bar`` word instead.


Upgrade to WeeChat 3.2
----------------------

Starting from WeeChat 3.2 full XDG paths were implemented, so that there
potentially will be a need to move your replacement definition file to move to
the new location.

For now, you can do nothing, replacer data file will be still looked in old
location, or you can move it to the new location.

If you decide to the migration, default location for the replacement map
file will be the ``$weechat_data_dir`` which in most of the cases would be
``~/.local/share/weechat``, unless you;re using ``--dir`` or ``--temp-dir``
weechats params.

Anyway, if you plan to do the full migration to XDG, and you had your
replacement definition file in ``~/.weechat/replacement_map.json``, and want to
move to the XDG location, than you'll want to move your configuration to
``$XDG_DATA_HOME/weechat``, which usually is ``~/.local/share/weechat`` before
removing old location. Note, that migrating instructions only applies to the
replacer plugin. For WeeChat itself, you'll need to consult WeeChat
documentation.


License
-------

This plugin is on Apache 2 license. See LICENSE for details.
