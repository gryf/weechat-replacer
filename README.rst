weechat-replacer
================

Weechat plugin for replacing user defined keywords with specified text.

Installation and configuration
------------------------------

In order to use it, you have to have Weechat with Python plugin support
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

License
-------

This plugin is on Apache 2 license. See LICENSE for details.
