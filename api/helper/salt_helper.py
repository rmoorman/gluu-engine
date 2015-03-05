# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2015 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def create_key_store():
    # salt supresses the flask logger, hence we import salt inside
    # this function as a workaround
    import salt.config
    import salt.key

    salt_opts = salt.config.client_config("/etc/salt/master")
    key_store = salt.key.Key(salt_opts)
    return key_store


def register_minion(key):
    """Registers a minion.

    :param key: Key used by minion; typically a container ID (short format)
    """
    # accepts minion's key
    key_store = create_key_store()
    return key_store.accept(key)


def unregister_minion(key):
    """Unregisters a minion.

    :param key: Key used by minion; typically a container ID (short format)
    """
    # deletes minion's key
    key_store = create_key_store()
    return key_store.delete_key(key)
