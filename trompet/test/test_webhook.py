import json
import string
import unittest

try:
    from unittest.mock import Mock, call
except ImportError:
    from mock import Mock, call

from twisted.web.test.requesthelper import DummyRequest

from trompet.listeners.webhook import WebhookListener, extract_bitbucket_commit


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


class WebHookListenerTest(unittest.TestCase):
    def _commit_extractor(self, payload, commit):
        return commit

    def _create_listener(self, limit=None):
        observer = Mock()
        message_format = string.Template("$rev")
        listener = WebhookListener(
            "project", observer, message_format, self._commit_extractor, limit)
        return (observer, listener)

    def _create_request(self, number_of_commits):
        body = {
            "commits": [{"rev": i} for i in range(number_of_commits)]
        }
        request = DummyRequest([b"/"])
        request.method = "POST"
        request.args["payload"] = [json.dumps(body)]
        return request

    def test_unlimited_messages(self):
        (observer, listener) = self._create_listener(limit=None)
        request = self._create_request(10)
        listener.render_POST(request)
        # Should really be a 200 instead of None, but DummyRequest does
        # not set 200 as default :(
        self.assertEqual(request.responseCode, None)
        expected = [call.notify('project', str(i)) for i in range(10)]
        self.assertEqual(observer.mock_calls, expected)

    def test_omitted_messages(self):
        (observer, listener) = self._create_listener(limit=3)
        request = self._create_request(4)
        listener.render_POST(request)
        # Should really be a 200 instead of None, but DummyRequest does
        # not set 200 as default :(
        self.assertEqual(request.responseCode, None)
        expected = [call.notify('project', str(i)) for i in range(3)]
        expected.append(call.notify('project', '[1 commits omitted.]'))
        self.assertEqual(observer.mock_calls, expected)

    def test_exactly_number_of_limit_commits(self):
        (observer, listener) = self._create_listener(limit=3)
        request = self._create_request(3)
        listener.render_POST(request)
        # Should really be a 200 instead of None, but DummyRequest does
        # not set 200 as default :(
        self.assertEqual(request.responseCode, None)
        expected = [call.notify('project', str(i)) for i in range(3)]
        self.assertEqual(observer.mock_calls, expected)
