import pickle
import os

from tests.mocker import MockerTestCase

from smart import sysconf
from smart.sysconfig import SysConfig
from smart.plugins import landscape


CLIENT_CONF = """
[client]
http_proxy = http://proxy.url
https_proxy = https://proxy.url
ftp_proxy = ftp://proxy.url
"""

EMPTY_CLIENT_CONF = """
[client]
"""


class LandscapePluginTest(MockerTestCase):

    def setUp(self):
        self.sysconf_state = pickle.dumps(sysconf.object)
        sysconf.object = SysConfig()

        self.original_client_conf_path = landscape.CLIENT_CONF_PATH
        self.client_conf_path = self.makeFile(CLIENT_CONF)
        landscape.CLIENT_CONF_PATH = self.client_conf_path

    def tearDown(self):
        sysconf.object = pickle.loads(self.sysconf_state)
        landscape.CLIENT_CONF_PATH = self.original_client_conf_path

    def write_client_conf(self, content):
        file = open(self.client_conf_path, "w")
        file.write(content)
        file.close()

    def test_default_landscape_config_file_path(self):
        self.assertEquals(self.original_client_conf_path,
                          "/etc/landscape/client.conf")

    def test_nothing_happens_if_not_explicitly_enabled(self):
        landscape.run()
        self.assertEquals(sysconf.get("http-proxy"), None)
        self.assertEquals(sysconf.get("https-proxy"), None)
        self.assertEquals(sysconf.get("ftp-proxy"), None)

    def test_use_proxies_set_in_landscape(self):
        """
        If enabled, the landscape smart plugin will read the proxies
        set in Landscape.
        """
        sysconf.set("use-landscape-proxies", True)
        landscape.run()
        self.assertEquals(sysconf.get("http-proxy"), "http://proxy.url")
        self.assertEquals(sysconf.get("https-proxy"), "https://proxy.url")
        self.assertEquals(sysconf.get("ftp-proxy"), "ftp://proxy.url")

    def test_nothing_happens_if_there_are_no_proxy_settings(self):
        """
        The default settings won't be touched if there are no
        proxy options in the client configuration.
        """
        self.write_client_conf(EMPTY_CLIENT_CONF)
        sysconf.set("use-landscape-proxies", True)
        landscape.run()
        self.assertEquals(sysconf.get("http-proxy"), None)
        self.assertEquals(sysconf.get("https-proxy"), None)
        self.assertEquals(sysconf.get("ftp-proxy"), None)

    def test_nothing_happens_if_there_is_no_section(self):
        """
        The default settings won't be touched if there are no
        proxy options in the client configuration.
        """
        self.write_client_conf("")
        sysconf.set("use-landscape-proxies", True)
        landscape.run()
        self.assertEquals(sysconf.get("http-proxy"), None)
        self.assertEquals(sysconf.get("https-proxy"), None)
        self.assertEquals(sysconf.get("ftp-proxy"), None)

    def test_when_missing_do_not_override_existing_options(self):
        """
        If there are existing settings, they won't be overriden if
        the Landscape client didn't provide any options.
        """
        sysconf.set("http-proxy", "http-url")
        sysconf.set("https-proxy", "https-url")
        sysconf.set("ftp-proxy", "ftp-url")

        self.write_client_conf(EMPTY_CLIENT_CONF)
        sysconf.set("use-landscape-proxies", True)
        landscape.run()

        self.assertEquals(sysconf.get("http-proxy"), "http-url")
        self.assertEquals(sysconf.get("https-proxy"), "https-url")
        self.assertEquals(sysconf.get("ftp-proxy"), "ftp-url")

    def test_doesnt_break_on_unexisting_file(self):
        os.unlink(self.client_conf_path)
        sysconf.set("use-landscape-proxies", True)
        landscape.run()
        self.assertEquals(sysconf.get("http-proxy"), None)
        self.assertEquals(sysconf.get("https-proxy"), None)
        self.assertEquals(sysconf.get("ftp-proxy"), None)