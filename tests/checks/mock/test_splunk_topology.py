# stdlib
import json

from checks import CheckException
from tests.checks.common import AgentCheckTest, Fixtures

def _mocked_saved_searches(*args, **kwargs):
    return []

class TestSplunkNoTopology(AgentCheckTest):
    """
    Splunk check should work in absence of topology
    """
    CHECK_NAME = 'splunk_topology'

    def test_checks(self):
        self.maxDiff = None

        config = {
            'init_config': {},
            'instances': [
                {
                    'url': 'http://localhost:8089',
                    'username': "admin",
                    'password': "admin",
                    'component_saved_searches': [],
                    'relation_saved_searches': []
                }
            ]
        }
        self.run_check(config, mocks={'_saved_searches':_mocked_saved_searches})
        instances = self.check.get_topology_instances()
        self.assertEqual(len(instances), 1)


# Sid is equal to search name
def _mocked_dispatch_saved_search(*args, **kwargs):
    return args[1].name


def _mocked_search(*args, **kwargs):
    # sid is set to saved search name
    sid = args[0]
    return [json.loads(Fixtures.read_file("%s.json" % sid))]


class TestSplunkTopology(AgentCheckTest):
    """
    Splunk check should work with component and relation data
    """
    CHECK_NAME = 'splunk_topology'

    def test_checks(self):
        self.maxDiff = None

        config = {
            'init_config': {},
            'instances': [
                {
                    'url': 'http://localhost:8089',
                    'username': "admin",
                    'password': "admin",
                    'component_saved_searches': [{
                        "name": "components",
                        "parameters": {}
                    }],
                    'relation_saved_searches': [{
                        "name": "relations",
                        "parameters": {}
                    }],
                    'tags': ['mytag', 'mytag2']
                }
            ]
        }

        self.run_check(config, mocks={
            '_dispatch_saved_search': _mocked_dispatch_saved_search,
            '_search': _mocked_search,
            '_saved_searches': _mocked_saved_searches
        })

        instances = self.check.get_topology_instances()
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]['instance'], {"type":"splunk","url":"http://localhost:8089"})

        self.assertEqual(instances[0]['components'][0], {
            "externalId": u"vm_2_1",
            "type": {"name": u"vm"},
            "data": {
                u"running": True,
                u"_time": u"2017-03-06T14:55:54.000+00:00",
                "label.label1Key": "label1Value",
                "tags": ['result_tag1', 'mytag', 'mytag2']
            }
        })

        self.assertEqual(instances[0]['components'][1], {
            "externalId": u"server_2",
            "type": {"name": u"server"},
            "data": {
                u"description": u"My important server 2",
                u"_time": u"2017-03-06T14:55:54.000+00:00",
                "label.label2Key": "label2Value",
                "tags": ['result_tag2', 'mytag', 'mytag2']
            }
        })

        self.assertEquals(instances[0]['relations'][0], {
            "externalId": u"vm_2_1-HOSTED_ON-server_2",
            "type": {"name": u"HOSTED_ON"},
            "sourceId": u"vm_2_1",
            "targetId": u"server_2",
            "data": {
                u"description": u"Some relation",
                u"_time": u"2017-03-06T15:10:57.000+00:00",
                "tags": ['mytag', 'mytag2']
            }
        })

        self.assertEquals(self.service_checks[0]['status'], 0, "service check should have status AgentCheck.OK")


def _mocked_minimal_search(*args, **kwargs):
    # sid is set to saved search name
    sid = args[0]
    return [json.loads(Fixtures.read_file("minimal_%s.json" % sid))]


class TestSplunkMinimalTopology(AgentCheckTest):
    """
    Splunk check should work with minimal component and relation data
    """
    CHECK_NAME = 'splunk_topology'

    def test_checks(self):
        self.maxDiff = None

        config = {
            'init_config': {},
            'instances': [
                {
                    'url': 'http://localhost:8089',
                    'username': "admin",
                    'password': "admin",
                    'component_saved_searches': [{
                        "name": "components",
                        "element_type": "component",
                        "parameters": {}
                    }],
                    'relation_saved_searches': [{
                        "name": "relations",
                        "element_type": "relation",
                        "parameters": {}
                    }],
                    'tags': ['mytag', 'mytag2']
                }
            ]
        }

        self.run_check(config, mocks={
            '_dispatch_saved_search': _mocked_dispatch_saved_search,
            '_search': _mocked_minimal_search,
            '_saved_searches': _mocked_saved_searches
        })

        instances = self.check.get_topology_instances()
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]['instance'], {"type":"splunk","url":"http://localhost:8089"})

        self.assertEqual(instances[0]['components'][0], {
            "externalId": u"vm_2_1",
            "type": {"name": u"vm"},
            "data": {
                "tags": ['mytag', 'mytag2']
            }
        })

        self.assertEqual(instances[0]['components'][1], {
            "externalId": u"server_2",
            "type": {"name": u"server"},
            "data": {
                "tags": ['mytag', 'mytag2']
            }
        })

        self.assertEquals(instances[0]['relations'][0], {
            "externalId": u"vm_2_1-HOSTED_ON-server_2",
            "type": {"name": u"HOSTED_ON"},
            "sourceId": u"vm_2_1",
            "targetId": u"server_2",
            "data": {
                "tags": ['mytag', 'mytag2']
            }
        })

        self.assertEquals(self.service_checks[0]['status'], 0, "service check should have status AgentCheck.OK")


def _mocked_incomplete_search(*args, **kwargs):
    # sid is set to saved search name
    sid = args[0]
    return [json.loads(Fixtures.read_file("incomplete_%s.json" % sid))]


class TestSplunkIncompleteTopology(AgentCheckTest):
    """
    Splunk check should crash on incomplete data
    """
    CHECK_NAME = 'splunk_topology'

    def test_checks(self):
        self.maxDiff = None

        config = {
            'init_config': {},
            'instances': [
                {
                    'url': 'http://localhost:8089',
                    'username': "admin",
                    'password': "admin",
                    'component_saved_searches': [{
                        "name": "components",
                        "element_type": "component",
                        "parameters": {}
                    }],
                    'relation_saved_searches': [{
                        "name": "relations",
                        "element_type": "relation",
                        "parameters": {}
                    }],
                    'tags': ['mytag', 'mytag2']
                }
            ]
        }

        thrown = False
        try:
            self.run_check(config, mocks={
                '_dispatch_saved_search': _mocked_dispatch_saved_search,
                '_search': _mocked_incomplete_search,
                '_saved_searches': _mocked_saved_searches
            })
        except CheckException:
            thrown = True
        self.assertTrue(thrown, "Retrieving incomplete data from splunk should throw")

        self.assertEquals(self.service_checks[0]['status'], 2, "service check should have status AgentCheck.CRITICAL")


class TestSplunkPollingInterval(AgentCheckTest):
    """
    Test whether the splunk check properly implements the polling intervals
    """
    CHECK_NAME = 'splunk_topology'

    def test_checks(self):
        self.maxDiff = None

        config = {
            'init_config': {},
            'instances': [
                {
                    'url': 'http://localhost:8089',
                    'username': "admin",
                    'password': "admin",
                    'component_saved_searches': [{
                        "name": "components_fast",
                        "element_type": "component",
                        "parameters": {}
                    }],
                    'relation_saved_searches': [{
                        "name": "relations_fast",
                        "element_type": "relation",
                        "parameters": {}
                    }],
                    'tags': ['mytag', 'mytag2']
                },
                {
                    'url': 'http://remotehost:8089',
                    'username': "admin",
                    'password': "admin",
                    'polling_interval_seconds': 30,
                    'component_saved_searches': [{
                        "name": "components_slow",
                        "element_type": "component",
                        "parameters": {}
                    }],
                    'relation_saved_searches': [{
                        "name": "relations_slow",
                        "element_type": "relation",
                        "parameters": {}
                    }],
                    'tags': ['mytag', 'mytag2']
                }
            ]
        }

        # Used to validate which searches have been executed
        test_data = {
            "expected_searches": [],
            "time": 0,
            "throw": False
        }

        def _mocked_current_time_seconds():
            return test_data["time"]

        def _mocked_interval_search(*args, **kwargs):
            if test_data["throw"]:
                raise CheckException("Is broke it")

            sid = args[0]
            self.assertTrue(sid in test_data["expected_searches"])
            return [json.loads(Fixtures.read_file("empty.json"))]

        test_mocks = {
            '_dispatch_saved_search': _mocked_dispatch_saved_search,
            '_search': _mocked_interval_search,
            '_current_time_seconds': _mocked_current_time_seconds,
            '_saved_searches': _mocked_saved_searches
        }

        # Inital run
        test_data["expected_searches"] = ["components_fast", "relations_fast", "components_slow", "relations_slow"]
        test_data["time"] = 1
        self.run_check(config, mocks=test_mocks)
        self.check.get_topology_instances()

        # Only fast ones after 15 seconds
        test_data["expected_searches"] = ["components_fast", "relations_fast"]
        test_data["time"] = 20
        self.run_check(config, mocks=test_mocks)
        self.check.get_topology_instances()

        # Slow ones after 40 seconds aswell
        test_data["expected_searches"] = ["components_fast", "relations_fast", "components_slow", "relations_slow"]
        test_data["time"] = 40
        self.run_check(config, mocks=test_mocks)
        self.check.get_topology_instances()

        # Nothing should happen when throwing
        test_data["expected_searches"] = []
        test_data["time"] = 60
        test_data["throw"] = True

        thrown = False
        try:
            self.run_check(config, mocks=test_mocks)
        except CheckException:
            thrown = True
        self.check.get_topology_instances()
        self.assertTrue(thrown, "Expect thrown to be done from the mocked search")
        self.assertEquals(self.service_checks[0]['status'], 2, "service check should have status AgentCheck.CRITICAL")

        # Updating should happen asap after throw
        test_data["expected_searches"] = ["components_fast", "relations_fast"]
        test_data["time"] = 61
        test_data["throw"] = False
        self.run_check(config, mocks=test_mocks)
        self.check.get_topology_instances()

        self.assertEquals(self.service_checks[0]['status'], 0, "service check should have status AgentCheck.OK")

class TestSplunkErrorResponse(AgentCheckTest):
    """
    Splunk check should handle a FATAL message response
    """
    CHECK_NAME = 'splunk_topology'

    def test_checks(self):
        self.maxDiff = None

        config = {
            'init_config': {},
            'instances': [
                {
                    'url': 'http://localhost:8089',
                    'username': "admin",
                    'password': "admin",
                    'component_saved_searches': [{
                        "name": "error",
                        "element_type": "component",
                        "parameters": {}
                    }],
                    'relation_saved_searches': [],
                    'tags': ['mytag', 'mytag2']
                }
            ]
        }

        thrown = False
        try:
            self.run_check(config, mocks={
                '_dispatch_saved_search': _mocked_dispatch_saved_search,
                '_search': _mocked_search,
                '_saved_searches': _mocked_saved_searches
            })
        except CheckException:
            thrown = True
        self.assertTrue(thrown, "Retrieving FATAL message from Splunk should throw.")

        self.assertEquals(self.service_checks[0]['status'], 2, "service check should have status AgentCheck.CRITICAL")

class TestSplunkWildcardTopology(AgentCheckTest):
    """
    Splunk check should work with component and relation data
    """
    CHECK_NAME = 'splunk_topology'

    def test_checks(self):
        self.maxDiff = None

        config = {
            'init_config': {},
            'instances': [
                {
                    'url': 'http://localhost:8089',
                    'username': "admin",
                    'password': "admin",
                    'polling_interval_seconds': 0,
                    'component_saved_searches': [{
                        "match": "comp.*",
                        "parameters": {}
                    }],
                    'relation_saved_searches': [{
                        "match": "rela.*",
                        "parameters": {}
                    }],
                    'tags': ['mytag', 'mytag2']
                }
            ]
        }

        data = {
            'saved_searches': []
        }

        def _mocked_saved_searches(*args, **kwargs):
            return data['saved_searches']

        # Add the saved searches
        data['saved_searches'] = ["components", "relations"]
        self.run_check(config, mocks={
            '_dispatch_saved_search': _mocked_dispatch_saved_search,
            '_search': _mocked_search,
            '_saved_searches': _mocked_saved_searches
        })
        instances = self.check.get_topology_instances()
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]['instance'], {"type":"splunk","url":"http://localhost:8089"})
        self.assertEqual(len(instances[0]['components']), 2)
        self.assertEquals(len(instances[0]['relations']), 1)

        self.assertEquals(self.service_checks[0]['status'], 0, "service check should have status AgentCheck.OK")

        # Remove the saved searches
        data['saved_searches'] = []
        self.run_check(config, mocks={
            '_dispatch_saved_search': _mocked_dispatch_saved_search,
            '_search': _mocked_search,
            '_saved_searches': _mocked_saved_searches
        })
        instances = self.check.get_topology_instances()
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]['instance'], {"type":"splunk","url":"http://localhost:8089"})
        self.assertEqual(len(instances[0]['components']), 0)
        self.assertEquals(len(instances[0]['relations']), 0)

        self.assertEquals(self.service_checks[0]['status'], 0, "service check should have status AgentCheck.OK")
