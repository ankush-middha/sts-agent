# stdlib
import unittest

# 3p
import mock
import json
from requests.exceptions import HTTPError, ConnectionError, Timeout
from requests import Response

# project
from utils.splunk.splunk_helper import SplunkHelper
from checks import FinalizeException


class FakeInstanceConfig(object):
    def __init__(self):
        self.base_url = 'http://testhost:8089'
        self.default_request_timeout_seconds = 10
        self.verify_ssl_certificate = False
        self.ignore_saved_search_errors = True

    def get_auth_tuple(self):
        return ('username', 'password')


class FakeResponse(object):
    def __init__(self, text, status_code=200, headers={}):
        self.status_code = status_code
        self.payload = text
        self.headers = headers
        self.content = text

    def json(self):
        return json.loads(self.payload)

    def raise_for_status(self):
        return

class mocked_saved_search:
    """
    A Mocked Saved Search Object
    """
    def __init__(self):
        self.name = "components"
        self.request_timeout_seconds = 10

class MockResponse(Response):
    """
    A Mocked Response for request_session post method
    """
    def __init__(self, json_data):
        Response.__init__(self)
        self.json_data = json_data
        self.status_code = json_data["status_code"]
        self.reason = json_data["reason"]
        self.url = json_data["url"]

    def json(self):
        return self.json_data


class TestSplunkHelper(unittest.TestCase):
    """
    Test the Splunk Helper class
    """

    @mock.patch('utils.splunk.splunk_helper.SplunkHelper._do_post', return_value=FakeResponse("""{ "sessionKey": "MySessionKeyForThisSession" }""", headers={}))
    def test_auth_session_fallback(self, mocked_do_post):
        """
        Test request authentication on fallback Authentication header
        retrieve auth session key,
        set it to the requests session,
        and see whether the outgoing request contains the expected HTTP header
        The expected HTTP header is Authentication when Set-Cookie is not present
        """
        helper = SplunkHelper(FakeInstanceConfig())
        helper.auth_session()

        mocked_do_post.assert_called_with("/services/auth/login?output_mode=json", "username=username&password=password&cookie=1", 10)
        mocked_do_post.assert_called_once()

        expected_header = helper.requests_session.headers.get("Authentication")
        self.assertEqual(expected_header, "Splunk MySessionKeyForThisSession")

    def test_dispatch_with_ignore_saved_search_errors_true(self):
        """
        Test dispatch method to get value None in case of flag ignore_saved_search_errors=True
        """

        path = '/servicesNS/%s/%s/saved/searches/%s/dispatch' % ("admin", "search", "component")
        helper = SplunkHelper(FakeInstanceConfig())

        # Mock the post response of request_session
        helper.requests_session.post = mock.MagicMock()
        helper.requests_session.post.return_value = MockResponse({"reason": "Not Found", "status_code": 404, "url": path})

        res = helper.dispatch(mocked_saved_search(), "admin", "search", helper.instance_config.ignore_saved_search_errors, None)

        self.assertEqual(res, None)

    def test_dispatch_with_ignore_saved_search_errors_false(self):
        """
        Test dispatch method to get value None in case of flag ignore_saved_search_errors=False
        """

        path = '/servicesNS/%s/%s/saved/searches/%s/dispatch' % ("admin", "search", "component")
        helper = SplunkHelper(FakeInstanceConfig())
        helper.instance_config.ignore_saved_search_errors = False

        # Mock the post response of request_session
        helper.requests_session.post = mock.MagicMock()
        helper.requests_session.post.return_value = MockResponse({"reason": "Not Found", "status_code": 404, "url": path})

        self.assertRaises(HTTPError, helper.dispatch, mocked_saved_search(), "admin", "search", helper.instance_config.ignore_saved_search_errors, None)

    def test_finalize_sid(self):
        """
        Test finalize_sid method to successfully pass
        """
        url = FakeInstanceConfig().base_url
        helper = SplunkHelper(FakeInstanceConfig())
        helper.requests_session.post = mock.MagicMock()
        helper.requests_session.post.return_value = FakeResponse(status_code=200, text="done")
        # return None when response is 200
        self.assertEqual(helper.finalize_sid("admin_comp1", mocked_saved_search()), None)

        helper.requests_session.post.return_value = MockResponse({"reason": "Unknown Sid", "status_code": 404, "url": url})
        # return None when sid not found because we want to continue
        self.assertEqual(helper.finalize_sid("admin_comp1", mocked_saved_search()), None)

        helper.requests_session.post.return_value = MockResponse({"reason": "Internal Server error", "status_code": 500, "url": url})
        # return finalize exception when api returns 500
        self.assertRaises(FinalizeException, helper.finalize_sid, "admin_comp1", mocked_saved_search())

        helper.requests_session.post = mock.MagicMock(side_effect=Timeout())
        # return finalize exception when timeout occurs
        self.assertRaises(FinalizeException, helper.finalize_sid, "admin_comp1", mocked_saved_search())

        helper.requests_session.post = mock.MagicMock(side_effect=ConnectionError())
        # return finalize exception when connection error occurs
        self.assertRaises(FinalizeException, helper.finalize_sid, "admin_comp1", mocked_saved_search())
