# -*- coding: utf-8 -*-
import tempfile
import codecs

try:
    from cStringIO import StringIO
except:
    from io import StringIO

from django.core.management import call_command

from cms.test_utils.fixtures.navextenders import NavextendersFixture
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.models import Page, Placeholder, CMSPlugin


class FixtureTestCase(NavextendersFixture, SettingsOverrideTestCase):

    def test_fixture_load(self):
        """
        This test dumps a live set of pages, cleanup the database and load it
        again.
        This makes fixtures unnecessary and it's easier to maintain.
        """
        output = StringIO()
        dump = tempfile.mkstemp(".json")
        call_command('dumpdata', 'cms', indent=3, stdout=output)
        original_ph = Placeholder.objects.count()
        original_pages = Page.objects.count()
        original_plugins = CMSPlugin.objects.count()
        Page.objects.all().delete()
        output.seek(0)
        with codecs.open(dump[1], 'w', 'utf-8') as dumpfile:
            dumpfile.write(output.read())

        self.assertEqual(0, Page.objects.count())
        self.assertEqual(0, Placeholder.objects.count())
        # Transaction disable, otherwise the connection it the test would be
        # isolated from the data loaded in the different command connection
        call_command('loaddata', dump[1], commit=False, stdout=output)
        self.assertEqual(10, Page.objects.count())
        self.assertEqual(original_pages, Page.objects.count())
        # Placeholder number may differ if signals does not correctly handle
        # load data command
        self.assertEqual(original_ph, Placeholder.objects.count())
        self.assertEqual(original_plugins, CMSPlugin.objects.count())
