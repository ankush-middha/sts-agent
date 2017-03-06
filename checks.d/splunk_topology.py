"""
    StackState.
    Splunk topology extraction
"""

# 3rd party
import requests
from urllib import quote
import json
import httplib as http_client
import logging

# project
from checks import AgentCheck, CheckException


class SplunkTopology(AgentCheck):
    INSTANCE_TYPE = "splunk"
    SERVICE_CHECK_NAME = "splunk.topology_information"
    service_check_needed = True

    def check(self, instance):
        if 'url' not in instance:
            raise Exception('Splunk topology instance missing "url" value.')

        base_url = instance['url']

        instance_key = {
            "type": self.INSTANCE_TYPE,
            "url": base_url
        }

        instance_tags = instance.get('tags', [])
        default_timeout = self.init_config.get('default_timeout', 5)
        timeout = float(instance.get('timeout', default_timeout))

        self.start_snapshot(instance_key)

        sid = self._dispatch_saved_search(base_url, "saved_test")

        print "using sid: " + sid

        import time
        time.sleep(5)

        self._search(base_url, sid)

        self.stop_snapshot(instance_key)

    def _search(self, base_url, sid):
        search_url = '%s/services/search/jobs/%s/results?output_mode=json' % (base_url, sid)
        timeout = None # TODO fix timeout

        auth = ("admin", "admin") # TODO

        response = requests.get(search_url, auth=auth).json()
        print response

    def _dispatch_saved_search(self, base_url, saved_search_name):
        "{{baseurl}}/services/saved/searches/{{saved_search_name}}/dispatch"

        dispatch_url = '%s/services/saved/searches/%s/dispatch' % (base_url, quote(saved_search_name))
        print dispatch_url

        auth = ("admin", "admin")
        payload = {
            'force_dispatch': True,
            'output_mode': 'json',
            'dispatch.now': True
        }

        response_body = self._do_post(dispatch_url, auth, payload).json()
        return response_body['sid']

    def _do_post(self, url, auth, payload):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        http_client.HTTPConnection.debuglevel = 1

        # You must initialize logging, otherwise you'll not see debug output.
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

        # TODO add timeout=DEFAULT_API_REQUEST_TIMEOUT

        print "json:"+ json.dumps(payload)

        resp = requests.post(url, headers=headers, data=payload, auth=auth)
        resp.raise_for_status()
        return resp
