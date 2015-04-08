#!/usr/bin/env python
import os

os.environ['EVE_SETTINGS'] = "%s%s" % (os.environ['OPENSHIFT_REPO_DIR'],
                                       'server/settings.py')
from server.app import app as application
