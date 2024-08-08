import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import json
from elasticsearch import Elasticsearch, helpers
from datetime import datetime
from pathlib import Path

# Assuming the methods are in a file named `curator.py`
from curator import (
    verifyAndGetVar, get_data_from_file, convertCertificateDatesToUTC,
    bulk_json_data, push_data_to_elasticsearch, append_timestamp_to_es_document,
    logger, indexName, es
)


class TestCuratorMethods(unittest.TestCase):

    @patch('os.getenv')
    @patch('curator.logger')
    def test_verifyAndGetVar(self, mock_logger, mock_getenv):
        # Mocking os.getenv to return None
        mock_getenv.return_value = None
        with self.assertRaises(SystemExit):
            verifyAndGetVar('MISSING_VAR')
        mock_logger.error.assert_called_once()

        # Mocking os.getenv to return a value
        mock_getenv.return_value = 'value'
        result = verifyAndGetVar('EXISTING_VAR')
        self.assertEqual(result, 'value')

    @patch('pathlib.Path.open')
    def test_get_data_from_file(self, mock_open):
        # Mocking the JSON file content
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps([{"key": "value"}])
        result = get_data_from_file('mock_file.json')
        self.assertEqual(result, [{"key": "value"}])

    def test_convertCertificateDatesToUTC(self):
        doc = {
            'end_date': '2023-08-01 12:00:00',
            'start_date': '2023-01-01 00:00:00'
        }
        result = convertCertificateDatesToUTC(doc)
        self.assertIsInstance(result['certificate_end_date'], datetime)
        self.assertIsInstance(result['certificate_start_date'], datetime)
        self.assertEqual(result['certificate_end_date'], datetime(2023, 8, 1, 12, 0, 0))
        self.assertEqual(result['certificate_start_date'], datetime(2023, 1, 1, 0, 0, 0))

    @patch('curator.get_data_from_file')
    def test_bulk_json_data(self, mock_get_data_from_file):
        # Mocking the JSON data
        mock_get_data_from_file.return_value = [{'end_date': '2023-08-01 12:00:00', 'start_date': '2023-01-01 00:00:00'}]
        generator = bulk_json_data('mock_file.json', 'mock_index', 'mock_type')
        doc = next(generator)
        self.assertIn('_index', doc)
        self.assertIn('_type', doc)
        self.assertIn('_id', doc)
        self.assertIn('_source', doc)

    @patch('curator.helpers.bulk')
    @patch('curator.bulk_json_data')
    @patch('curator.logger')
    def test_push_data_to_elasticsearch(self, mock_logger, mock_bulk_json_data, mock_bulk):
        # Mocking bulk to return a response
        mock_bulk.return_value = 'mock_response'
        push_data_to_elasticsearch()
        mock_logger.info.assert_called_once()
        mock_bulk.assert_called_once()

    def test_append_timestamp_to_es_document(self):
        doc = {}
        append_timestamp_to_es_document(doc)
        self.assertIn('timestamp', doc)
        self.assertIsInstance(doc['timestamp'], str)

if __name__ == '__main__':
    unittest.main()
