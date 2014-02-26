# -*- coding: utf-8 -*-
from __future__ import with_statement
import hashlib

from django.utils.encoding import iri_to_uri, force_text
from django.contrib.auth.views import redirect_to_login
from django.template.response import TemplateResponse
from cms.apphook_pool import apphook_pool
from cms.appresolver import get_app_urls
from cms.models import Title, Page
from cms.utils import get_template_from_request, get_language_from_request, get_cms_setting
from cms.utils.i18n import get_fallback_languages, force_language, get_public_languages, get_redirect_on_fallback, \
    get_language_list, is_language_prefix_patterns_used
from cms.utils.page_resolver import get_page_from_request
from cms.test_utils.util.context_managers import SettingsOverride
from django.conf import settings
from django.conf.urls import patterns
from django.core.urlresolvers import resolve, Resolver404, reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.template.context import RequestContext
from django.utils.http import urlquote
from django.utils.timezone import get_current_timezone_name


CMS_PAGE_CACHE_VERSION_KEY = 'CMS_PAGE_CACHE_VERSION'

def _handle_no_page(request, slug):
    if not slug and settings.DEBUG:
        return TemplateResponse(request, "cms/welcome.html", RequestContext(request))
    raise Http404('CMS: Page not found for "%s"' % slug)


def details(request, slug):
    """
    The main view of the Django-CMS! Takes a request and a slug, renders the
    page.
    """
    from django.core.cache import cache

    if get_cms_setting("PAGE_CACHE") and (not hasattr(request, 'toolbar') or (
                    not request.toolbar.edit_mode and not request.toolbar.show_toolbar and not request.user.is_authenticated())):
        cache_content = cache.get(
            _get_cache_key(request),
            version=_get_cache_version()
        )
        if not cache_content is None:
            content, headers = cache_content
            response = HttpResponse(content)
            response._headers = headers
            return response

    # get the right model
    context = RequestContext(request)
    # Get a Page model object from the request
    page = get_page_from_request(request, use_path=slug)
    if not page:
        return _handle_no_page(request, slug)

    current_language = get_language_from_request(request)
    # Check that the current page is available in the desired (current) language
    available_languages = []
    page_languages = list(page.get_languages())
    if hasattr(request, 'user') and request.user.is_staff:
        user_languages = get_language_list()
    else:
        user_languages = get_public_languages()
    for frontend_lang in user_languages:
        if frontend_lang in page_languages:
            available_languages.append(frontend_lang)
    attrs = ''
    if 'edit' in request.GET:
        attrs = '?edit=1'
    elif 'preview' in request.GET:
        attrs = '?preview=1'
        if 'draft' in request.GET:
            attrs += '&draft=1'
            # Check that the language is in FRONTEND_LANGUAGES:
    if not current_language in user_languages:
        #are we on root?
        if not slug:
            #redirect to supported language
            languages = []
            for language in available_languages:
                languages.append((language, language))
            if languages:
                with SettingsOverride(LANGUAGES=languages, LANGUAGE_CODE=languages[0][0]):
                    #get supported language
                    new_language = get_language_from_request(request)
                    if new_language in get_public_languages():
                        with force_language(new_language):
                            pages_root = reverse('pages-root')
                            return HttpResponseRedirect(pages_root + attrs)
            else:
                _handle_no_page(request, slug)
        else:
            return _handle_no_page(request, slug)
    if current_language not in available_languages:
        # If we didn't find the required page in the requested (current)
        # language, let's try to find a fallback
        found = False
        for alt_lang in get_fallback_languages(current_language):
            if alt_lang in available_languages:
                if get_redirect_on_fallback(current_language):
                    with force_language(alt_lang):
                        path = page.get_absolute_url(language=alt_lang, fallback=True)
                        # In the case where the page is not available in the
                    # preferred language, *redirect* to the fallback page. This
                    # is a design decision (instead of rendering in place)).
                    return HttpResponseRedirect(path + attrs)
                else:
                    found = True
        if not found:
            # There is a page object we can't find a proper language to render it
            _handle_no_page(request, slug)

    if apphook_pool.get_apphooks():
        # There are apphooks in the pool. Let's see if there is one for the
        # current page
        # since we always have a page at this point, applications_page_check is
        # pointless
        # page = applications_page_check(request, page, slug)
        # Check for apphooks! This time for real!
        try:
            app_urls = page.get_application_urls(current_language, False)
        except Title.DoesNotExist:
            app_urls = []
        skip_app = False
        if not page.is_published(current_language) and request.toolbar.edit_mode:
            skip_app = True
        if app_urls and not skip_app:
            app = apphook_pool.get_apphook(app_urls)
            pattern_list = []
            for urlpatterns in get_app_urls(app.urls):
                pattern_list += urlpatterns
            urlpatterns = patterns('', *pattern_list)
            try:
                view, args, kwargs = resolve('/', tuple(urlpatterns))
                return view(request, *args, **kwargs)
            except Resolver404:
                pass
                # Check if the page has a redirect url defined for this language.
    redirect_url = page.get_redirect(language=current_language)
    if redirect_url:
        if (is_language_prefix_patterns_used() and redirect_url[0] == "/" and not redirect_url.startswith(
                    '/%s/' % current_language)):
            # add language prefix to url
            redirect_url = "/%s/%s" % (current_language, redirect_url.lstrip("/"))
            # prevent redirect to self
        own_urls = [
            'http%s://%s%s' % ('s' if request.is_secure() else '', request.get_host(), request.path),
            '/%s' % request.path,
            request.path,
        ]
        if redirect_url not in own_urls:
            return HttpResponseRedirect(redirect_url + attrs)

    # permission checks
    if page.login_required and not request.user.is_authenticated():
        return redirect_to_login(urlquote(request.get_full_path()), settings.LOGIN_URL)

    template_name = get_template_from_request(request, page, no_current_page=True)
    # fill the context 
    context['lang'] = current_language
    context['current_page'] = page
    context['has_change_permissions'] = page.has_change_permission(request)
    context['has_view_permissions'] = page.has_view_permission(request)

    if not context['has_view_permissions']:
        return _handle_no_page(request, slug)

    response = TemplateResponse(request, template_name, context)

    response.add_post_render_callback(_cache_page)

    # Add headers for X Frame Options - this really should be changed upon moving to class based views
    xframe_options = page.get_xframe_options()
    if xframe_options == Page.X_FRAME_OPTIONS_INHERIT:
        # This is when we defer to django's own clickjacking handling
        return response

    # We want to prevent django setting this in their middlewear
    response.xframe_options_exempt = True

    if xframe_options == Page.X_FRAME_OPTIONS_ALLOW:
        # Do nothing, allowed is no header.
        return response
    elif xframe_options == Page.X_FRAME_OPTIONS_SAMEORIGIN:
        response['X-Frame-Options'] = 'SAMEORIGIN'
    elif xframe_options == Page.X_FRAME_OPTIONS_DENY:
        response['X-Frame-Options'] = 'DENY'

    return response


def _cache_page(response):
    from django.core.cache import cache

    if not get_cms_setting('PAGE_CACHE'):
        return response
    request = response._request
    save_cache = True
    if hasattr(request, 'placeholders'):
        for placeholder in request.placeholders:
            if not placeholder.cache_placeholder:
                save_cache = False
                break
    if hasattr(request, 'toolbar'):
        if request.toolbar.edit_mode or request.toolbar.show_toolbar:
            save_cache = False
    if request.user.is_authenticated():
        save_cache = False
    if not save_cache:
        response
    if save_cache:
        version = _get_cache_version()
        ttl = get_cms_setting('CACHE_DURATIONS')['content']

        cache.set(
            _get_cache_key(request),
            (response.content, response._headers),
            ttl,
            version=version
        )
        # See note in invalidate_cms_page_cache()
        cache.set(
            CMS_PAGE_CACHE_VERSION_KEY,
            version,
            ttl
        )
    

def _get_cache_key(request):
    #md5 key of current path
    cache_key = "%s:%s" % (
        get_cms_setting("CACHE_PREFIX"),
        hashlib.md5(iri_to_uri(request.get_full_path()).encode('utf-8')).hexdigest()
    )
    if settings.USE_TZ:
        # The datetime module doesn't restrict the output of tzname().
        # Windows is known to use non-standard, locale-dependant names.
        # User-defined tzinfo classes may return absolutely anything.
        # Hence this paranoid conversion to create a valid cache key.
        tz_name = force_text(get_current_timezone_name(), errors='ignore')
        cache_key += '.%s' % tz_name.encode('ascii', 'ignore').decode('ascii').replace(' ', '_')
    return cache_key

def _get_cache_version():
    from django.core.cache import cache

    '''
    Returns the current page cache version, explicitly setting one if not
    defined.
    '''

    version = cache.get(CMS_PAGE_CACHE_VERSION_KEY)

    if version:
        return version
    else:
        cache.set(
            CMS_PAGE_CACHE_VERSION_KEY,
            1,
            get_cms_setting('CACHE_DURATIONS')['content']
        )
        return 1


def invalidate_cms_page_cache():
    from django.core.cache import cache

    '''
    Invalidates the CMS PAGE CACHE.
    '''

    #
    # NOTE: We're using a cache versioning strategy for invalidating the page
    # cache when necessary. Instead of wiping all the old entries, we simply
    # increment the version number rendering all previous entries
    # inaccessible and left to expire naturally.
    #
    # ALSO NOTE: According to the Django documentation, a timeout value of
    # `None' (in version 1.6+) is supposed to mean "cache forever", however,
    # this is actually only implemented as only slightly less than 30 days in
    # some backends (memcached, in particular). In older Djangos, `None' means
    # "use default value".  To avoid issues arising from different Django
    # versions and cache backend implementations, we will explicitly set the
    # lifespan of the CMS_PAGE_CACHE_VERSION entry to whatever is set in
    # settings.CACHE_DURATIONS['content']. This allows users to adjust as
    # necessary for their backend.
    #
    # To prevent writing cache entries that will live longer than our version
    # key, we will always re-write the current version number into the cache
    # just after we write any new cache entries, thus ensuring that the
    # version number will always outlive any entries written against that
    # version. This is a cheap operation.
    #
    # If there are no new cache writes before the version key expires, its
    # perfectly OK, since any previous entries cached against that version
    # will have also expired, so, it'd be pointless to try to access them
    # anyway.
    #
    try:
        cache.incr(CMS_PAGE_CACHE_VERSION_KEY)
    except ValueError:
        # Key doesn't exist, so just set it to the default
        cache.set(CMS_PAGE_CACHE_VERSION_KEY, 1, get_cms_setting('CACHE_DURATIONS')['content'])
