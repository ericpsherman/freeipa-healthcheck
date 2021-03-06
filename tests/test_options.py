#
# Copyright (C) 2022 FreeIPA Contributors see COPYING for license
#

import argparse
import io
import logging
import os
import tempfile
from contextlib import redirect_stdout
from unittest.mock import patch

from ipahealthcheck.core.core import RunChecks
from ipahealthcheck.core.plugin import Results

options = argparse.Namespace(check=None, source=None, debug=False,
                             indent=2, list_sources=False,
                             output_type='json', output_file=None,
                             verbose=False, version=False, config=None)


@patch('ipahealthcheck.core.core.run_service_plugins')
@patch('ipahealthcheck.core.core.run_plugins')
@patch('ipahealthcheck.core.core.parse_options')
def test_options_merge(mock_parse, mock_run, mock_service):
    """
    Test merging file-based and CLI options
    """
    mock_service.return_value = (Results(), [])
    mock_run.return_value = Results()
    mock_parse.return_value = options
    fd, config_path = tempfile.mkstemp()
    os.close(fd)
    with open(config_path, "w") as fd:
        fd.write('[default]\n')
        fd.write('output_type=human\n')
        fd.write('indent=5\n')

    try:
        run = RunChecks(['ipahealthcheck.registry'], config_path)

        run.run_healthcheck()

        # verify two valus that have defaults with our overriden values
        assert run.options.output_type == 'human'
        assert run.options.indent == 5
    finally:
        os.remove(config_path)


@patch('ipahealthcheck.core.core.run_service_plugins')
@patch('ipahealthcheck.core.core.run_plugins')
@patch('ipahealthcheck.core.core.parse_options')
def test_cfg_file_debug_option(mock_parse, mock_run, mock_service):
    """
    Test if the debug option is respected in the configuration file

    Related: https://bugzilla.redhat.com/show_bug.cgi?id=2079861
    """
    mock_service.return_value = (Results(), [])
    mock_run.return_value = Results()
    mock_parse.return_value = options
    fd, config_path = tempfile.mkstemp()
    os.close(fd)
    with open(config_path, "w") as fd:
        fd.write('[default]\n')
        fd.write('debug=True\n')

    try:
        run = RunChecks([], config_path)
        run.run_healthcheck()

        assert run.options.debug
    finally:
        os.remove(config_path)


@patch('ipahealthcheck.core.core.run_service_plugins')
@patch('ipahealthcheck.core.core.run_plugins')
@patch('ipahealthcheck.core.core.parse_options')
def test_incorrect_output_type_cfg_file(mock_parse, mock_run, mock_service):
    """
    Test the error message is user-friendly if the incorrect output type is
    provided in cfg file

    Related: https://bugzilla.redhat.com/show_bug.cgi?id=2079698
    """
    mock_service.return_value = (Results(), [])
    mock_run.return_value = Results()
    mock_parse.return_value = options
    fd, config_path = tempfile.mkstemp()
    os.close(fd)
    with open(config_path, "w") as fd:
        fd.write('[default]\n')
        fd.write('output_type=42\n')

    try:
        run = RunChecks([], config_path)

        f = io.StringIO()
        with redirect_stdout(f):
            run.run_healthcheck()

        assert "Unknown output-type" in f.getvalue()

    finally:
        os.remove(config_path)


@patch('ipahealthcheck.core.core.run_service_plugins')
@patch('ipahealthcheck.core.core.run_plugins')
@patch('ipahealthcheck.core.core.parse_options')
def test_incorrect_delimiter_cfg_file(mock_parse, mock_run, mock_service,
                                      caplog):
    """
    Test the error message is user-friendly if the incorrect delimiter is
    used in cfg file

    Related: https://bugzilla.redhat.com/show_bug.cgi?id=2079739
    """
    mock_service.return_value = (Results(), [])
    mock_run.return_value = Results()
    mock_parse.return_value = options
    fd, config_path = tempfile.mkstemp()
    os.close(fd)
    with open(config_path, "w") as fd:
        fd.write('[default]\n')
        fd.write('output_type;human\n')

    try:
        run = RunChecks([], config_path)

        with caplog.at_level(logging.ERROR):
            run.run_healthcheck()

        assert "contains parsing errors" in caplog.text

    finally:
        os.remove(config_path)
