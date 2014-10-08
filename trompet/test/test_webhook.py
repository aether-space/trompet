import unittest

from trompet.listeners.webhook import extract_bitbucket_commit

class BitbucketTest(unittest.TestCase):
    def test_extract_commit(self):
        commit_data = {
            "node": "a73056d1d557",
            "files": [{"type": "added", "file": "foo"}],
            "branch": "default",
            "author": "Author",
            "timestamp": "2011-04-20 21:28:41",
            "raw_node": "a73056d1d557ea61fae786bf71a2d5427cf46893",
            "parents": [],
            "raw_author": "Test User <test@example.org>",
            "message": "Test commit message",
            "size": 0,
            "revision": 0
        }
        data = {
            "repository": {
                "absolute_url": "/Test/test/"
            }
        }
        expected = {
            "author": "Author",
            "revision": "a73056d1d557",
            "branch": "default",
            "message": "Test commit message",
            "shortmessage": "Test commit message",
            "url": "https://bitbucket.org/Test/test/changeset/a73056d1d557"
        }
        self.assertEqual(extract_bitbucket_commit(data, commit_data), expected)
