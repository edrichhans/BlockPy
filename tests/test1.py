import unittest
import os
import os.path
import shutil

#python -m unittest discover -s tests

class UnitTests(unittest.TestCase):
	def test_import_package(self):
		import hashMe
		import nacl.encoding
		import nacl.signing
		import nacl.hash
		import blockpy_logging
		import getpass

	def test_db_connection(self):
		import psycopg2
		import config
		params = config.config()
		conn = psycopg2.connect(**params)

		self.assertTrue(conn)

if __name__ == "__main__":
    unittest.main()