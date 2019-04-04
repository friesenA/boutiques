#!/usr/bin/env python

from boutiques import __file__ as bfile
from boutiques.bosh import bosh
from unittest import TestCase
from boutiques.dataHandler import ZenodoError
import os
import mock

class TestDataHandler(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile), "schema", "examples")

    def test_inspect(self):
        output = bosh(["data", "inspect", "-e"])
        breakpoint()

        seed_cache_dir()

        output = bosh(["data", "inspect"])
        breakpoint()

        output = bosh(["data", "inspect", "-e"])
        breakpoint()

        cleanup()

    @mock.patch('os.listdir', return_value=)
    @mock.patch('os.remove', )
    def test_discard(self):

        seed_cache_dir()

        with self.assertRaises(ValueError) as e:
            bosh(["data", "delete", "-f", "bad-filename"])
        self.assertIn("File bad-filename does not exist in the data cache"
                      , str(e.exception))

        result = bosh(["data", "delete", "-f", "testrecord1"])

        with self.assertRaises(ValueError) as e:
            bosh(["data", "delete"])
        self.assertIn("Must indicate a file to discard", str(e.exception))

        result = bosh(["data", "delete", "-a"])

        cleanup()
