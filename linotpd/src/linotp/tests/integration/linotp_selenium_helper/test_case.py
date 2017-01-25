# -*- coding: utf-8 -*-
#
#    LinOTP - the open source solution for two factor authentication
#    Copyright (C) 2010 - 2017 KeyIdentity GmbH
#
#    This file is part of LinOTP server.
#
#    This program is free software: you can redistribute it and/or
#    modify it under the terms of the GNU Affero General Public
#    License, version 3, as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the
#               GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#    E-mail: linotp@keyidentity.com
#    Contact: www.linotp.org
#    Support: www.keyidentity.com
#
import unittest
import logging

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from helper import get_from_tconfig
from realm import RealmManager
from policy import PolicyManager
from user_id_resolver import UserIdResolverManager

logger = logging.getLogger(__name__)

class TestCase(unittest.TestCase):
    """Basic LinOTP TestCase class"""

    implicit_wait_time = 5

    @classmethod
    def setUpClass(cls):
        """Initializes the base_url and sets the driver"""

        cls.http_username = get_from_tconfig(['linotp', 'username'], required=True)
        cls.http_password = get_from_tconfig(['linotp', 'password'], required=True)
        cls.http_host = get_from_tconfig(['linotp', 'host'], required=True)
        cls.http_protocol = get_from_tconfig(['linotp', 'protocol'], default="https")
        cls.http_port = get_from_tconfig(['linotp', 'port'])
        cls.base_url = cls.http_protocol + "://" + cls.http_username + \
            ":" + cls.http_password + "@" + cls.http_host
        if cls.http_port:
            cls.base_url += ":" + cls.http_port

        remote_setting = get_from_tconfig(['selenium', 'remote'], default='False')
        remote_enable = remote_setting.lower() == 'true'
        remote_url = get_from_tconfig(['selenium', 'remote_url'])

        cls.driver = None
        selenium_driver = get_from_tconfig(['selenium', 'driver'],
                                           default="firefox").lower()
        selenium_driver_language = get_from_tconfig(['selenium', 'language'],
                                                    default="en_us").lower()
        def _get_chrome_options():
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--lang=' + selenium_driver_language)
            return chrome_options

        def _get_firefox_profile():
            fp = webdriver.FirefoxProfile()
            fp.set_preference("intl.accept_languages", selenium_driver_language)
            return fp

        if not remote_enable:
            if selenium_driver == 'chrome':
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument('--lang=' + selenium_driver_language)

                try:
                    cls.driver = webdriver.Chrome(chrome_options=_get_chrome_options())
                except WebDriverException, e:
                    logger.error("Error creating Chrome driver. Maybe you need to install"
                                  " 'chromedriver'. If you wish to use another browser please"
                                  " adapt your configuratiion file. Error message: %s" % str(e))
                    raise

            elif selenium_driver == 'firefox':
                cls.driver = webdriver.Firefox(firefox_profile=_get_firefox_profile())

            if cls.driver is None:
                warnings.warn("Falling back to Firefox driver.")
                cls.driver = webdriver.Firefox(firefox_profile=_get_firefox_profile())
        else:
            # Remote driver. We need to build a desired capabilities
            # request for the remote instance

            # Map the requested driver to the remote capabilities
            # listed in selenium.webdriver.DesiredCapabilities
            #  e.g. firefox -> FIREFOX

            selenium_driver = selenium_driver.upper()

            try:
                desired_capabilities = getattr(DesiredCapabilities, selenium_driver).copy()
            except AttributeError:
                logger.warning("Could not find capabilities for the given remote driver %s", selenium_driver)
                desired_capabilities = {'browserName': selenium_driver}

            # Remote driver
            if not remote_url:
                remote_url = 'http://127.0.0.1:4444/wd/hub'

            try:
                cls.driver = webdriver.Remote(command_executor=remote_url,
                                               desired_capabilities=desired_capabilities)
            except Exception as e:
                logger.error("Could not start driver: %s", e)
                raise

    def setUp(self):
        self.enableImplicitWait()
        self.verification_errors = []
        self.accept_next_alert = True

    def tearDown(self):
        """Closes the driver and displays all errors"""
        self.assertEqual([], self.verification_errors)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def disableImplicitWait(self):
        self.driver.implicitly_wait(0)

    def enableImplicitWait(self):
        self.driver.implicitly_wait(self.implicit_wait_time)

    def find_children_by_id(self, parent_id, element_type='*'):
        """
        Find an element with the given id, and return a list of children. The
        child list can be empty.
        """
        # Retrieve all elements including parent. This bypasses the timeout
        # that would other wise occur
        WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, parent_id))
            )

        self.disableImplicitWait()
        try:
            elements = WebDriverWait(self.driver, 0).until(
                    EC.presence_of_all_elements_located((By.XPATH, 'id("%s")//%s' % (parent_id, element_type)))
                )
        except TimeoutException:
            return []
        finally:
            self.enableImplicitWait()

        return elements  # Return elements without the parent

    def reset_resolvers_and_realms(self, resolver=None, realm=None):
        """
        Clear resolvers and realms. Then optionally create a userIdResolver with
        given data and add it to a realm of given name.
        """
        self.realm_manager = RealmManager(self)
        self.realm_manager.clear_realms()

        self.useridresolver_manager = UserIdResolverManager(self)
        self.useridresolver_manager.clear_resolvers()

        if resolver:
            self.useridresolver_manager.create_resolver(resolver)

            if realm:
                self.realm_manager.open()
                self.realm_manager.create(realm, resolver['name'])
                self.realm_manager.close()
        else:
            assert not realm, "Can't create a realm without a resolver"


    def reset_policies(self):
        """
        Remove all policies
        """
        self.policy_manager = PolicyManager(self.driver, self.base_url)
        self.policy_manager.clear_policies()

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True
