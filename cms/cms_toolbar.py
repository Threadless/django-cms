# -*- coding: utf-8 -*-
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch, resolve, Resolver404
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sites.models import Site

from cms.api import get_page_draft
from cms.compat import user_model_label
from cms.constants import TEMPLATE_INHERITANCE_MAGIC, PUBLISHER_STATE_PENDING
from cms.models import Title, Page
from cms.toolbar.items import TemplateItem
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.compat import DJANGO_1_4
from cms.utils.i18n import get_language_tuple, force_language
from cms.utils import get_cms_setting
from cms.utils.permissions import get_user_sites_queryset, has_page_change_permission
from menus.utils import DefaultLanguageChanger


# Identifiers for search
ADMIN_MENU_IDENTIFIER = 'admin-menu'
LANGUAGE_MENU_IDENTIFIER = 'language-menu'
TEMPLATE_MENU_BREAK = 'Template Menu Break'
PAGE_MENU_IDENTIFIER = 'page'
PAGE_MENU_ADD_IDENTIFIER = 'add_page'
PAGE_MENU_FIRST_BREAK = 'Page Menu First Break'
PAGE_MENU_SECOND_BREAK = 'Page Menu Second Break'
PAGE_MENU_THIRD_BREAK = 'Page Menu Third Break'
PAGE_MENU_FOURTH_BREAK = 'Page Menu Fourth Break'
PAGE_MENU_LAST_BREAK = 'Page Menu Last Break'
HISTORY_MENU_IDENTIFIER = 'history'
HISTORY_MENU_BREAK = 'History Menu Break'
MANAGE_PAGES_BREAK = 'Manage Pages Break'
ADMIN_SITES_BREAK = 'Admin Sites Break'
ADMINISTRATION_BREAK = 'Administration Break'
USER_SETTINGS_BREAK = 'User Settings Break'
ADD_PAGE_LANGUAGE_BREAK = "Add page language Break"
REMOVE_PAGE_LANGUAGE_BREAK = "Remove page language Break"
COPY_PAGE_LANGUAGE_BREAK = "Copy page language Break"


@toolbar_pool.register
class PlaceholderToolbar(CMSToolbar):
    """
    Adds placeholder edit buttons if placeholders or static placeholders are detected in the template

    """

    def post_template_populate(self):
        self.page = get_page_draft(self.request.current_page)
        statics = getattr(self.request, 'static_placeholders', [])
        placeholders = getattr(self.request, 'placeholders', [])
        if self.page:
            if self.page.has_change_permission(self.request):
                self.add_structure_mode()
            elif statics:
                for static_placeholder in statics:
                    if static_placeholder.has_change_permission(self.request):
                        self.add_structure_mode()
                        break
        else:
            added = False
            if statics:
                for static_placeholder in statics:
                    if static_placeholder.has_change_permission(self.request):
                        self.add_structure_mode()
                        added = True
                        break
            if not added and placeholders:
                self.add_structure_mode()

    def add_structure_mode(self):
        switcher = self.toolbar.add_button_list('Mode Switcher', side=self.toolbar.RIGHT,
                                                extra_classes=['cms_toolbar-item-cms-mode-switcher'])
        switcher.add_button(_("Structure"), '?%s' % get_cms_setting('CMS_TOOLBAR_URL__BUILD'), active=self.toolbar.build_mode,
                            disabled=not self.toolbar.build_mode)
        switcher.add_button(_("Content"), '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'), active=not self.toolbar.build_mode,
                            disabled=self.toolbar.build_mode)


@toolbar_pool.register
class BasicToolbar(CMSToolbar):
    """
    Basic Toolbar for site and languages menu
    """

    def populate(self):
        self.add_admin_menu()
        if settings.USE_I18N:
            self.add_language_menu()

    def add_admin_menu(self):
        admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, self.current_site.name)
        if self.request.user.has_perm('user.change_user') and User in admin.site._registry:
            admin_menu.add_sideframe_item(_('Users'), url=reverse(
                "admin:" + user_model_label.replace('.', '_').lower() + "_changelist"))
            # sites menu
        if get_cms_setting('PERMISSION'):
            sites_queryset = get_user_sites_queryset(self.request.user)
        else:
            sites_queryset = Site.objects.all()
        if len(sites_queryset) > 1:
            sites_menu = admin_menu.get_or_create_menu('sites', _('Sites'))
            sites_menu.add_sideframe_item(_('Admin Sites'), url=reverse('admin:sites_site_changelist'))
            sites_menu.add_break(ADMIN_SITES_BREAK)
            for site in sites_queryset:
                sites_menu.add_link_item(site.name, url='http://%s' % site.domain,
                                         active=site.pk == self.current_site.pk)
                # admin
        admin_menu.add_sideframe_item(_('Administration'), url=reverse('admin:index'))
        admin_menu.add_break(ADMINISTRATION_BREAK)
        # cms users
        admin_menu.add_sideframe_item(_('User settings'), url=reverse('admin:cms_usersettings_change'))
        admin_menu.add_break(USER_SETTINGS_BREAK)
        # logout
        # If current page is not published or has view restrictions user is
        # redirected to the home page:
        # * published page: no redirect
        # * unpublished page: redirect to the home page
        # * published page with login_required: redirect to the home page
        # * published page with view permissions: redirect to the home page
        if self.request.current_page:
            if not self.request.current_page.is_published(self.current_lang):
                page = self.request.current_page
            else:
                page = self.request.current_page.get_public_object()
        else:
            page = None
        redirect_url = '/'

        #
        # We'll show "Logout Joe Bloggs" if the name fields in auth.User are
        # completed, else "Logout jbloggs". If anything goes wrong, it'll just
        # be "Logout".
        #
        try:
            if self.request.user.get_full_name():
                user_name = self.request.user.get_full_name()
            else:
                if DJANGO_1_4:
                    user_name = self.request.user.username
                else:
                    user_name = self.request.user.get_username()
        except:
            user_name = ''

        if user_name:
            logout_menu_text = _('Logout %s') % user_name
        else:
            logout_menu_text = _('Logout')

        if (page and
            (not page.is_published(self.current_lang) or page.login_required
                or not page.has_view_permission(self.request, AnonymousUser()))):
            on_success = redirect_url
        else:
            on_success = self.toolbar.REFRESH_PAGE

        admin_menu.add_ajax_item(
            logout_menu_text,
            action=reverse('admin:logout'),
            active=True,
            on_success=on_success
        )

    def add_language_menu(self):
        language_menu = self.toolbar.get_or_create_menu(LANGUAGE_MENU_IDENTIFIER, _('Language'))
        language_changer = getattr(self.request, '_language_changer', DefaultLanguageChanger(self.request))
        for code, name in get_language_tuple(self.current_site.pk):
            try:
                url = language_changer(code)
            except NoReverseMatch:
                url = DefaultLanguageChanger(self.request)(code)
            language_menu.add_link_item(name, url=url, active=self.current_lang == code)


@toolbar_pool.register
class PageToolbar(CMSToolbar):
    watch_models = [Page]

    # Helpers

    def init_from_request(self):
        self.page = get_page_draft(self.request.current_page)
        self.title = self.get_title()
        self.placeholders = getattr(self.request, 'placeholders', [])
        self.statics = getattr(self.request, 'static_placeholders', [])
        self.dirty_statics = [sp for sp in self.statics if sp.dirty]
        self.permissions_activated = get_cms_setting('PERMISSION')

    def get_title(self):
        try:
            return Title.objects.get(page=self.page, language=self.current_lang, publisher_is_draft=True)
        except Title.DoesNotExist:
            return None

    def has_publish_permission(self):
        if not hasattr(self, 'publish_permission'):
            publish_permission = bool(self.page or self.statics)

            if self.page:
                publish_permission = self.page.has_publish_permission(self.request)

            if self.statics:
                publish_permission &= all(sp.has_publish_permission(self.request) for sp in self.dirty_statics)

            self.publish_permission = publish_permission

        return self.publish_permission

    def has_page_change_permission(self):
        if not hasattr(self, 'page_change_permission'):
            # check global permissions if CMS_PERMISSIONS is active
            global_permission = self.permissions_activated and has_page_change_permission(self.request)

            # check if user has page edit permission
            page_permission = self.page and self.page.has_change_permission(self.request)

            self.page_change_permission = global_permission or page_permission

        return self.page_change_permission

    def page_is_pending(self, page, language):
        return (page.publisher_public_id and
                page.publisher_public.get_publisher_state(language) == PUBLISHER_STATE_PENDING)

    def in_apphook(self):
        with force_language(self.toolbar.language):
            try:
                resolver = resolve(self.request.path)
            except Resolver404:
                return False
            else:
                from cms.views import details
                return resolver.func != details

    def url_with_params(self, url, *args, **params):
        for arg in args:
            params.update(arg)
        if params:
            return '%s?%s' % (url, urlencode(params))
        return url

    # Populate

    def populate(self):
        self.init_from_request()
        self.change_admin_menu()
        self.add_page_menu()
        self.add_history_menu()
        self.change_language_menu()

    def post_template_populate(self):
        self.add_publish_button()
        self.add_draft_live()

    # Buttons

    def add_publish_button(self, classes=('cms_btn-action', 'cms_btn-publish',)):
        # only do dirty lookups if publish permission is granted else button isn't added anyway
        if self.toolbar.edit_mode and self.has_publish_permission():
            classes = list(classes or [])
            pk = self.page.pk if self.page else 0

            dirty = (bool(self.dirty_statics) or
                     (self.page and (self.page.is_dirty(self.current_lang) or
                                     self.page_is_pending(self.page, self.current_lang))))

            if dirty:
                classes.append('cms_btn-publish-active')

            if self.dirty_statics or (self.page and self.page.is_published(self.current_lang)):
                title = _('Publish changes')
            else:
                title = _('Publish page now')
                classes.append('cms_publish-page')

            params = {}

            if self.dirty_statics:
                params['statics'] = ','.join(str(sp.pk) for sp in self.dirty_statics)

            if self.in_apphook():
                params['redirect'] = self.request.path

            with force_language(self.current_lang):
                url = reverse('admin:cms_page_publish_page', args=(pk, self.current_lang))

            url = self.url_with_params(url, params)

            self.toolbar.add_button(title, url=url, extra_classes=classes,
                                    side=self.toolbar.RIGHT, disabled=not dirty)

    def add_draft_live(self):
        if self.page:
            if self.toolbar.edit_mode and not self.title:
                self.add_page_settings_button()

            if self.page.has_change_permission(self.request) and self.page.is_published(self.current_lang):
                return self.add_draft_live_item()

        elif self.placeholders:
            return self.add_draft_live_item()

        for sp in self.statics:
            if sp.has_change_permission(self.request):
                return self.add_draft_live_item()

    def add_draft_live_item(self, template='cms/toolbar/items/live_draft.html', extra_context=None):
        context = {'request': self.request}
        context.update(extra_context or {})
        pos = len(self.toolbar.right_items)
        self.toolbar.add_item(TemplateItem(template, extra_context=context, side=self.toolbar.RIGHT), position=pos)

    def add_page_settings_button(self, extra_classes=('cms_btn-action',)):
        url = '%s?language=%s' % (reverse('admin:cms_page_change', args=[self.page.pk]), self.toolbar.language)
        self.toolbar.add_modal_button(_('Page settings'), url, side=self.toolbar.RIGHT, extra_classes=extra_classes)

    # Menus

    def change_language_menu(self):
        if self.toolbar.edit_mode and self.page:
            language_menu = self.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
            if not language_menu:
                return None

            languages = get_language_tuple(self.current_site.pk)
            languages_dict = dict(languages)

            remove = [(code, languages_dict.get(code, code)) for code in self.page.get_languages()]
            add = [l for l in languages if l not in remove]
            copy = [(code, name) for code, name in languages if code != self.current_lang and (code, name) in remove]

            if add:
                language_menu.add_break(ADD_PAGE_LANGUAGE_BREAK)
                page_change_url = reverse('admin:cms_page_change', args=(self.page.pk,))
                title = _('Add %(language)s Translation')
                for code, name in add:
                    url = self.url_with_params(page_change_url, language=code)
                    language_menu.add_modal_item(title % {'language': name}, url=url)

            if remove:
                language_menu.add_break(REMOVE_PAGE_LANGUAGE_BREAK)
                translation_delete_url = reverse('admin:cms_page_delete_translation', args=(self.page.pk,))
                title = _('Delete %(language)s Translation')
                disabled = len(remove) == 1
                for code, name in remove:
                    url = self.url_with_params(translation_delete_url, language=code)
                    language_menu.add_modal_item(title % {'language': name}, url=url, disabled=disabled)

            if copy:
                language_menu.add_break(COPY_PAGE_LANGUAGE_BREAK)
                page_copy_url = reverse('admin:cms_page_copy_language', args=(self.page.pk,))
                title = _('Copy all plugins from %s')
                question = _('Are you sure you want copy all plugins from %s?')
                for code, name in copy:
                    language_menu.add_ajax_item(title % name, action=page_copy_url,
                                                data={'source_language': code, 'target_language': self.current_lang},
                                                question=question % name, on_success=self.toolbar.REFRESH_PAGE)

    def change_admin_menu(self):
        if self.has_page_change_permission():
            admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
            url = reverse('admin:cms_page_changelist')  # cms page admin
            params = {'language': self.toolbar.language}
            if self.page:
                params['page_id'] = self.page.pk
            url = self.url_with_params(url, params)
            admin_menu.add_sideframe_item(_('Pages'), url=url, position=0)

    def add_page_menu(self):
        if self.page and self.has_page_change_permission():
            edit_mode = self.toolbar.edit_mode
            refresh = self.toolbar.REFRESH_PAGE

            # menu for current page
            current_page_menu = self.toolbar.get_or_create_menu(PAGE_MENU_IDENTIFIER, _('Page'), position=1)

            # page operations menu
            add_page_menu = current_page_menu.get_or_create_menu(PAGE_MENU_ADD_IDENTIFIER, _('Add Page'))
            app_page_url = reverse('admin:cms_page_add')
            add_page_menu_sideframe_items = (
                (_('New Page'), {'edit': 1, 'position': 'last-child', 'target': self.page.parent_id or ''}),
                (_('New Sub Page'), {'edit': 1, 'position': 'last-child', 'target': self.page.pk}),
                (_('Duplicate this Page'), {'copy_target': self.page.pk})
            )

            for title, params in add_page_menu_sideframe_items:
                params.update(language=self.toolbar.language)
                add_page_menu.add_sideframe_item(title, url=self.url_with_params(app_page_url, params))

            # first break
            current_page_menu.add_break(PAGE_MENU_FIRST_BREAK)

            # page edit
            page_edit_url = '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
            current_page_menu.add_link_item(_('Edit this Page'), disabled=edit_mode, url=page_edit_url)

            # page settings
            page_settings_url = reverse('admin:cms_page_change', args=(self.page.pk,))
            page_settings_url = self.url_with_params(page_settings_url, language=self.toolbar.language)
            current_page_menu.add_modal_item(_('Page settings'), url=page_settings_url, disabled=not edit_mode,
                                             on_close=refresh)

            # templates menu
            if self.toolbar.build_mode or edit_mode:
                templates_menu = current_page_menu.get_or_create_menu('templates', _('Templates'))
                action = reverse('admin:cms_page_change_template', args=(self.page.pk,))
                for path, name in get_cms_setting('TEMPLATES'):
                    active = self.page.template == path
                    if path == TEMPLATE_INHERITANCE_MAGIC:
                        templates_menu.add_break(TEMPLATE_MENU_BREAK)
                    templates_menu.add_ajax_item(name, action=action, data={'template': path}, active=active,
                                                 on_success=refresh)

            # second break
            current_page_menu.add_break(PAGE_MENU_SECOND_BREAK)

            # advanced settings
            advanced_url = reverse('admin:cms_page_advanced', args=(self.page.pk,))
            advanced_url = self.url_with_params(advanced_url, language=self.toolbar.language)
            advanced_disabled = not self.page.has_advanced_settings_permission(self.request) or not edit_mode
            current_page_menu.add_modal_item(_('Advanced settings'), url=advanced_url, disabled=advanced_disabled)

            # permissions
            if self.permissions_activated:
                permissions_url = reverse('admin:cms_page_permissions', args=(self.page.pk,))
                permission_disabled = not edit_mode or not self.page.has_change_permissions_permission(self.request)
                current_page_menu.add_modal_item(_('Permissions'), url=permissions_url, disabled=permission_disabled)

            # dates settings
            dates_url = reverse('admin:cms_page_dates', args=(self.page.pk,))
            current_page_menu.add_modal_item(_('Publishing dates'), url=dates_url, disabled=not edit_mode)

            # third break
            current_page_menu.add_break(PAGE_MENU_THIRD_BREAK)

            # navigation toggle
            nav_title = _('Hide in navigation') if self.page.in_navigation else _('Display in navigation')
            nav_action = reverse('admin:cms_page_change_innavigation', args=(self.page.pk,))
            current_page_menu.add_ajax_item(nav_title, action=nav_action, disabled=not edit_mode, on_success=refresh)

            # publisher
            if self.title:
                if self.title.published:
                    publish_title = _('Unpublish page')
                    publish_url = reverse('admin:cms_page_unpublish', args=(self.page.pk, self.current_lang))
                else:
                    publish_title = _('Publish page')
                    publish_url = reverse('admin:cms_page_publish_page', args=(self.page.pk, self.current_lang))
                current_page_menu.add_ajax_item(publish_title, action=publish_url, disabled=not edit_mode,
                                                on_success=refresh)

            # fourth break
            current_page_menu.add_break(PAGE_MENU_FOURTH_BREAK)

            # delete
            delete_url = reverse('admin:cms_page_delete', args=(self.page.pk,))
            with force_language(self.current_lang):
                # We use force_language because it makes no sense to redirect a user
                # who just deleted a german page to an english page (user's default language)
                # simply because the url /en/some-german-page-slug will show nothing
                if self.page.parent:
                    # If this page has a parent, then redirect to it
                    on_delete_redirect_url = self.page.parent.get_absolute_url(language=self.current_lang)
                else:
                    # If there's no parent, we redirect to the root.
                    # Can't call Page.objects.get_home() because the user could very well delete the homepage
                    # causing get_home to throw an error.
                    # Let's keep in mind that if the user has deleted the last page, and django is running on
                    # DEBUG == False this redirect will cause a 404...
                    on_delete_redirect_url = reverse('pages-root')
            current_page_menu.add_modal_item(_('Delete page'), url=delete_url, on_close=on_delete_redirect_url,
                                             disabled=not edit_mode)

            # last break
            current_page_menu.add_break(PAGE_MENU_LAST_BREAK)

            # page type
            page_type_url = reverse('admin:cms_page_add_page_type')
            page_type_url = self.url_with_params(page_type_url, copy_target=self.page.pk, language=self.toolbar.language)
            current_page_menu.add_modal_item(_('Save as Page Type'), page_type_url, disabled=not edit_mode)

    def add_history_menu(self):
        if self.toolbar.edit_mode and self.page:
            refresh = self.toolbar.REFRESH_PAGE
            history_menu = self.toolbar.get_or_create_menu(HISTORY_MENU_IDENTIFIER, _('History'), position=2)

            if 'reversion' in settings.INSTALLED_APPS:
                import reversion
                from reversion.models import Revision

                versions = reversion.get_for_object(self.page)
                if self.page.revision_id:
                    current_revision = Revision.objects.get(pk=self.page.revision_id)
                    has_undo = versions.filter(revision__pk__lt=current_revision.pk).exists()
                    has_redo = versions.filter(revision__pk__gt=current_revision.pk).exists()
                else:
                    has_redo = False
                    has_undo = versions.count() > 1

                undo_action = reverse('admin:cms_page_undo', args=(self.page.pk,))
                redo_action = reverse('admin:cms_page_redo', args=(self.page.pk,))

                history_menu.add_ajax_item(_('Undo'), action=undo_action, disabled=not has_undo, on_success=refresh)
                history_menu.add_ajax_item(_('Redo'), action=redo_action, disabled=not has_redo, on_success=refresh)

                history_menu.add_break(HISTORY_MENU_BREAK)

            revert_action = reverse('admin:cms_page_revert_page', args=(self.page.pk, self.current_lang))
            revert_question = _('Are you sure you want to revert to live?')
            history_menu.add_ajax_item(_('Revert to live'), action=revert_action, question=revert_question,
                                       disabled=not self.page.is_dirty(self.current_lang), on_success=refresh)
            history_menu.add_modal_item(_('View history'), url=reverse('admin:cms_page_history', args=(self.page.pk,)))
