import unittest
from unittest.mock import patch, MagicMock
import logging
import os
import socket
import uuid

class TestLoggingBuilder(unittest.TestCase):

    @patch('logstash.TCPLogstashHandler')
    @patch('os.getenv')
    def test_build_logstash_handler(self, mock_getenv, mock_logstash_handler):
        mock_getenv.side_effect = lambda key: {'LOGSTASH_HOST': 'localhost', 'LOGSTASH_PORT': '5044'}.get(key)
        
        builder = LoggingBuilder()
        handler = builder.build_logstash_handler()

        mock_getenv.assert_any_call('LOGSTASH_HOST')
        mock_getenv.assert_any_call('LOGSTASH_PORT')
        mock_logstash_handler.assert_called_with('localhost', 5044, version=1)
        self.assertIsInstance(handler, MagicMock)

    @patch('logstash.TCPLogstashHandler')
    @patch('os.getenv')
    def test_build_application_logger(self, mock_getenv, mock_logstash_handler):
        mock_getenv.side_effect = lambda key: {'LOGSTASH_HOST': 'localhost', 'LOGSTASH_PORT': '5044'}.get(key)
        
        builder = LoggingBuilder()
        logger = builder.build_application_logger('test_logger')

        self.assertEqual(logger.name, 'test_logger')
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertTrue(any(isinstance(h, MagicMock) for h in logger.handlers))

    @patch('socket.gethostname')
    def test_format_additional_logs(self, mock_gethostname):
        mock_gethostname.return_value = 'test_host'
        builder = LoggingBuilder()

        extras = {
            'service.name': 'test_service',
            'service.environment': 'test_env',
            'service.org': 'test_org'
        }
        formatted_logs = builder.format_additional_logs(extras)

        self.assertEqual(formatted_logs['traceId'], builder.uniqid)
        self.assertEqual(formatted_logs['service.name'], 'test_service')
        self.assertEqual(formatted_logs['service.environment'], 'test_env')
        self.assertEqual(formatted_logs['service.org'], 'test_org')
        self.assertEqual(formatted_logs['service.hostname'], 'test_host')

        formatted_logs_empty = builder.format_additional_logs()
        self.assertEqual(formatted_logs_empty, {'traceId': builder.uniqid, 'service.hostname': 'test_host'})

class TestCuratorLogging(unittest.TestCase):

    @patch('LoggingBuilder')
    @patch('logging.getLogger')
    def setUp(self, mock_get_logger, mock_logging_builder):
        self.mock_logger = MagicMock()
        mock_get_logger.return_value = self.mock_logger
        self.mock_logging_builder = mock_logging_builder.return_value

        self.curator_logger = CuratorLogging('test_logger')

    def test_info(self):
        self.curator_logger.info('test_info_message')
        self.mock_logger.info.assert_called_once()
        args, kwargs = self.mock_logger.info.call_args
        self.assertEqual(args[0], 'test_info_message')

    def test_warn(self):
        self.curator_logger.warn('test_warn_message')
        self.mock_logger.warning.assert_called_once()
        args, kwargs = self.mock_logger.warning.call_args
        self.assertEqual(args[0], 'test_warn_message')

    def test_error(self):
        self.curator_logger.error('test_error_message')
        self.mock_logger.error.assert_called_once()
        args, kwargs = self.mock_logger.error.call_args
        self.assertEqual(args[0], 'test_error_message')


if __name__ == '__main__':
    unittest.main()
