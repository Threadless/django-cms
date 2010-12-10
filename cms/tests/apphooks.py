'''
Created on Dec 10, 2010

@author: jonas
'''
from __future__ import with_statement
from cms.apphook_pool import apphook_pool
from cms.tests.util.settings_contextmanager import SettingsOverride
from django.conf import settings
from django.test.testcases import TestCase


APP_NAME = 'SampleApp'

class ApphooksTestCase(TestCase):
    def test_01_explicit_apphooks(self):
        """
        Test explicit apphook loading with the CMS_APPHOOKS setting.
        """
        apphooks = (
            'testapp.sampleapp.cms_app.%s' % APP_NAME,
        )
        with SettingsOverride(CMS_APPHOOKS=apphooks):
            apphook_pool.clear()
            hooks = apphook_pool.get_apphooks()
            app_names = [hook[0] for hook in hooks]
            self.assertEqual(len(hooks), 1)
            self.assertEqual(app_names, [APP_NAME])
            apphook_pool.clear()