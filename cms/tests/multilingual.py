# -*- coding: utf-8 -*-
from cms.api import create_page, create_title, publish_page, add_plugin
from cms.test_utils.testcases import CMSTestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client


class MultilingualTestCase(CMSTestCase):

    def test_multilingual_page(self):
        page = create_page("mlpage", "nav_playground.html", "en")
        create_title("de", page.get_title(), page, slug=page.get_slug())
        page.rescan_placeholders()
        page = self.reload(page)
        placeholder = page.placeholders.all()[0]
        add_plugin(placeholder, "TextPlugin", 'de', body="test")
        add_plugin(placeholder, "TextPlugin", 'en', body="test")
        self.assertEqual(placeholder.cmsplugin_set.filter(language='de').count(), 1)
        self.assertEqual(placeholder.cmsplugin_set.filter(language='en').count(), 1)
        user = User.objects.create_superuser('super', 'super@django-cms.org', 'super')
        page = publish_page(page, user, True)
        public = page.publisher_public
        placeholder = public.placeholders.all()[0]
        self.assertEqual(placeholder.cmsplugin_set.filter(language='de').count(), 1)
        self.assertEqual(placeholder.cmsplugin_set.filter(language='en').count(), 1)

    def test_multiple_reverse_monkeypatch(self):
        """
        This test is not very well behaved, every following
        test that uses reverse will fail with a RuntimeException.
        """
        from cms.models import monkeypatch_reverse
        monkeypatch_reverse()
        monkeypatch_reverse()
        try:
            reverse('pages-root')
        except RuntimeError:
            self.fail('maximum recursion depth exceeded')

    def test_no_unnecessary_language_cookie(self):
        client = Client() # we need a fresh client to ensure no cookies are set
        response = client.get('/en/')
        self.assertIn('django_language', response.cookies)
        self.assertIn('sessionid', response.cookies)
        response = client.get('/')
        self.assertNotIn('django_language', response.cookies)
        self.assertNotIn('sessionid', response.cookies)
