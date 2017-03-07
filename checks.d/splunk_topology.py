"""
    StackState.
    Splunk topology extraction
"""

# 3rd party
import requests
from urllib import quote
import time

# project
from checks import AgentCheck, CheckException


class SavedSearch:
    def __init__(self, saved_search):
        self.name = saved_search['name']
        self.element_type = saved_search['element_type']
        self.parameters = saved_search['parameters']


class InstanceConfig:
    def __init__(self, instance, default_timeout):
        self.base_url = instance['url']
        self.username = instance['username']
        self.password = instance['password']
        self.timeout = float(instance.get('timeout', default_timeout))

    def get_auth_tuple(self):
        return self.username, self.password


class Instance:
    INSTANCE_TYPE = "splunk"

    def __init__(self, instance, default_timeout):
        self.instance_config = InstanceConfig(instance, default_timeout)
        self.saved_searches = [SavedSearch(saved_search) for saved_search in instance['saved_searches']]
        self.instance_key = {
            "type": self.INSTANCE_TYPE,
            "url": self.instance_config.base_url
        }
        self.tags = instance.get('tags', [])


class SplunkTopology(AgentCheck):
    # SERVICE_CHECK_NAME = "splunk.topology_information"
    # service_check_needed = True

    def check(self, instance):
        if 'url' not in instance:
            raise CheckException('Splunk topology instance missing "url" value.')

        default_timeout = self.init_config.get('default_timeout', 5)

        instance = Instance(instance, default_timeout)

        instance_key = instance.instance_key

        search_ids = [(self._dispatch_saved_search(instance.instance_config, saved_search), saved_search.element_type)
                      for saved_search in instance.saved_searches]

        self.start_snapshot(instance_key)

        for (sid, element_type) in search_ids:
            response = self._search(instance.instance_config, sid)
            if element_type == "component":
                self._extract_components(instance, response)
            elif element_type == "relation":
                self._extract_relations(instance, response)

        self.stop_snapshot(instance_key)


    def _search(self, instance_config, search_id):
        """
        perform a search operation on splunk given a search id (sid)
        :param instance_config: current check configuration
        :param search_id: perform a search operation on the search id
        :return: raw response from splunk
        """
        search_url = '%s/services/search/jobs/%s/results?output_mode=json' % (instance_config.base_url, search_id)
        auth = instance_config.get_auth_tuple()
        response = requests.get(search_url, auth=auth, timeout=instance_config.timeout)

        # retry until information is available.
        # TODO cap max amount of retries
        if response.status_code == 204: # HTTP No Content response
            time.sleep(2) # TODO move to config
            self._search(instance_config, search_id)

        return response.json()

    def _dispatch_saved_search(self, instance_config, saved_search):
        dispatch_url = '%s/services/saved/searches/%s/dispatch' % (instance_config.base_url, quote(saved_search.name))
        auth = instance_config.get_auth_tuple()

        parameters = saved_search.parameters[0]
        # json output_mode is mandatory for response parsing
        parameters["output_mode"] = "json"

        response_body = self._do_post(dispatch_url, auth, parameters, instance_config.timeout).json()
        return response_body['sid']

    def _do_post(self, url, auth, payload, timeout):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        resp = requests.post(url, headers=headers, data=payload, auth=auth, timeout=timeout)
        resp.raise_for_status()
        return resp

    # Get a field from a dictionary. Throw when it does not exist. When it exists, return it and remove from the object
    def _get_required_field(self, field, obj):
        if field not in obj:
            raise CheckException("Missing '%s' field in result data" % field)
        value = obj[field]
        del obj[field]
        return value

    def _extract_components(self, instance, result):
        for data in result["results"]:
            # Required fields
            external_id = self._get_required_field("id", data)
            comp_type = self._get_required_field("type", data)

            # We don't want to present the raw field
            if "_raw" in data:
                del data["_raw"]

            # Add tags to data
            if instance.tags:
                data['tags'] = instance.tags

            self.component(instance.instance_key, external_id, {"name": comp_type}, data)

    def _extract_relations(self, instance, result):
        for data in result["results"]:
            # Required fields
            rel_type = self._get_required_field("type", data)
            source_id = self._get_required_field("sourceId", data)
            target_id = self._get_required_field("targetId", data)

            # We don't want to present the raw field
            if "_raw" in data:
                del data["_raw"]

            # Add tags to data
            if instance.tags:
                data['tags'] = instance.tags

            self.relation(instance.instance_key, source_id, target_id, {"name": rel_type}, data)
