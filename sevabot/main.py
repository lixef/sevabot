# -*- coding: utf-8 -*-
"""

    Application entry point.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import imp
import sys
from hashlib import md5
import logging

from flask import Flask, request
import plac

from sevabot import modules

logger = logging.getLogger("sevabot")

# http://docs.python.org/library/logging.html
LOG_FORMAT = "%(message)s"

server = Flask(__name__)


@plac.annotations( \
    settings=("Settings file", 'option', 's', None, None, "settings.py"),
    )
def main(settings="settings.py"):
    """
    Application entry point.
    """

    # Expose settings global module
    settings = imp.load_source("settings", settings)

    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format=LOG_FORMAT)

    logger.info("Starting sevabot")

    modules.load_modules()

    # We do lazy import here, because
    # importing Skype4Py causes native DLL loading
    # and may cause random segfaults, Skype pop-up dialogs or
    # other unwanted side effects
    from sevabot.bot import Sevabot
    sevabot = Sevabot()

    logger.info("Skype API connection established")

    sevabot.start()
    server.run()

    #fuck cron stuff for now
    #interval = 1
    # while(True):
    #     time.sleep(interval)
    #     sevabot.runCron(interval)

    # Should be never reached
    return 0


@server.route("/cmd/<string:cmd>")
def command(cmd):
    try:
        return sevabot.runCmd(cmd).replace("\n", "<br />")
    except Exception as e:
        return str(e)


@server.route("/msg/", methods=['POST'])
def message():
    try:
        if request.method == 'POST':
            if ('chat' in request.form and
               'msg' in request.form and
               'md5' in request.form):

                chat = request.form['chat']
                msg = request.form['msg']
                m = request.form['md5']

                mcheck = md5(chat + msg + settings.SHARED_SECRET).hexdigest()
                if mcheck == m:
                    sevabot.sendMsg(chat, msg)
                else:
                    return "No can do %s\n" % (mcheck)
        return "Message sent"
    except Exception as e:
        return str(e)


def entry_point():
    exit_code = plac.call(main)
    return exit_code