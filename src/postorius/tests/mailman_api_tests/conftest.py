# Copyright (C) 2019-2023 by the Free Software Foundation, Inc.
#
# This file is part of Postorius
#
# mailman.client is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, version 3 of the License.
#
# mailman.client is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with mailman.client.  If not, see <http://www.gnu.org/licenses/>.

"""Testing utilities."""

import os
import shutil
import tempfile
from textwrap import dedent

import pytest
from mailman.config import config
from mailman.core import initialize
from mailman.core.initialize import INHIBIT_CONFIG_FILE
from mailman.testing.helpers import (
    TestableMaster,
    reset_the_world,
    wait_for_webservice,
)


@pytest.fixture(scope='session')
def config_initialize(request):
    # Set up the basic configuration stuff.  Turn off path creation until
    # we've pushed the testing config.
    config.create_paths = False
    initialize.initialize_1(INHIBIT_CONFIG_FILE)
    # Calculate a temporary VAR_DIR directory so that run-time artifacts
    # of the tests won't tread on the installation's data.  This also
    # makes it easier to clean up after the tests are done, and insures
    # isolation of test suite runs.
    var_dir = tempfile.mkdtemp()
    # We need a test configuration both for the foreground process and any
    # child processes that get spawned.  lazr.config would allow us to do
    # it all in a string that gets pushed, and we'll do that for the
    # foreground, but because we may be spawning processes (such as
    # runners) we'll need a file that we can specify to the with the -C
    # option.  Craft the full test configuration string here, push it, and
    # also write it out to a temp file for -C.
    #
    # Create a dummy postfix.cfg file so that the test suite doesn't try
    # to run the actual postmap command, which may not exist anyway.
    postfix_cfg = os.path.join(var_dir, 'postfix.cfg')
    with open(postfix_cfg, 'w') as fp:
        print(
            dedent(
                """
        [postfix]
        postmap_command: true
        transport_file_type: hash
        """
            ),
            file=fp,
        )
        test_config = dedent(
            """
        [mailman]
        layout: testing
        [paths.testing]
        var_dir: {}
        [mta]
        configuration: {}
        [devmode]
        enabled: yes
        testing: yes
        recipient: you@yourdomain.com

        [mta]
        smtp_port: 9025
        lmtp_port: 9024
        incoming: mailman.testing.mta.FakeMTA

        [webservice]
        port: 9001

        [archiver.mhonarc]
        enable: yes

        [archiver.mail_archive]
        enable: yes

        [archiver.prototype]
        enable: yes
        """.format(
                var_dir, postfix_cfg
            )
        )
        config.create_paths = True
        config.push('test config', test_config)
        # Initialize everything else.
    initialize.initialize_2(testing=True)
    initialize.initialize_3()

    config_file = os.path.join(var_dir, 'test.cfg')
    with open(config_file, 'w') as fp:
        fp.write(test_config)
        print(file=fp)
        config.filename = config_file
    # Start the Mailman's test runner.
    server = TestableMaster(wait_for_webservice)
    server.start('rest', 'in')
    request.addfinalizer(server.stop)
    # Run the test.
    yield
    reset_the_world()
    # Destroy the test database after the tests are done so that there is
    # no data in case the tests are rerun with a database layer like mysql
    # or postgresql which are not deleted in teardown.
    shutil.rmtree(var_dir)
    # Prevent the bit of post-processing on the .pop() that creates
    # directories.  We're basically shutting down everything and we don't
    # need the directories created.  Plus, doing so leaves a var directory
    # turd in the source tree's top-level directory.  We do it this way
    # rather than shutil.rmtree'ing the resulting var directory because
    # it's possible the user created a valid such directory for
    # operational or test purposes.
    config.create_paths = False
    config.pop('test config')


@pytest.fixture(scope='class', autouse=True)
def mailman_rest_layer(config_initialize, request):
    yield
    request.addfinalizer(reset_the_world)
