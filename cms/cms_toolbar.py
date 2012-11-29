# -*- coding: utf-8 -*-
import urllib
from cms.toolbar.base import Toolbar
from cms.toolbar.constants import LEFT, RIGHT
from cms.toolbar.items import (Anchor, Switcher, TemplateHTML, ListItem, List, 
    GetButton)
from cms.utils import cms_static_url
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from utils.permissions import has_page_change_permission


def _get_draft_page_id(toolbar):
    page = toolbar.request.current_page
    if page.publisher_is_draft:
        return page.pk
    else:
        return page.publisher_public_id

def _get_page_admin_url(context, toolbar, **kwargs):
    return reverse('admin:cms_page_change', args=(_get_draft_page_id(toolbar),))

def _get_page_history_url(context, toolbar, **kwargs):
    return reverse('admin:cms_page_history', args=(_get_draft_page_id(toolbar),))

def _get_add_child_url(context, toolbar, **kwargs):
    data = {
        'position': 'last-child',
        'target': _get_draft_page_id(toolbar),
    }
    args = urllib.urlencode(data)
    return '%s?%s' % (reverse('admin:cms_page_add'), args)

def _get_add_sibling_url(context, toolbar, **kwargs):
    data = {
        'position': 'last-child',
    }
    if toolbar.request.current_page.parent_id:
        data['target'] = toolbar.request.current_page.get_draft_object().parent_id
    args = urllib.urlencode(data)
    return '%s?%s' % (reverse('admin:cms_page_add'), args)

def _get_delete_url(context, toolbar, **kwargs):
    return reverse('admin:cms_page_delete', args=(_get_draft_page_id(toolbar),))

def _get_publish_url(context, toolbar, **kwargs):
    return reverse('admin:cms_page_publish_page', args=(_get_draft_page_id(toolbar),))

def _get_revert_url(context, toolbar, **kwargs):
    return reverse('admin:cms_page_revert_page', args=(_get_draft_page_id(toolbar),))

def _page_is_dirty(request):
    page = request.current_page
    return page and page.published and page.get_draft_object().is_dirty()


class CMSToolbar(Toolbar):
    """
    The default CMS Toolbar
    """
    revert_button = GetButton(RIGHT, 'revert', _("Revert"),
                              url=_get_revert_url, enable=_page_is_dirty)

    edit_mode_switcher = Switcher(LEFT, 'editmode', 'edit', 'edit-off',
                                  _('Edit mode'))

    @property
    def is_staff(self):
        return self.request.user.is_staff

    @property
    def can_change(self):
        return has_page_change_permission(self.request)

    @property
    def edit_mode(self):
        return self.is_staff and self.edit_mode_switcher.get_state(self.request)

    @property
    def show_toolbar(self):
        return self.is_staff or self.edit_mode_switcher.get_state(self.request)

    @property
    def current_page(self):
        return self.request.current_page

    def get_items(self, context, **kwargs):
        """
        Get the CMS items on the toolbar
        """
        items = [
            Anchor(LEFT, 'logo', _('django CMS'), 'https://www.django-cms.org'),
        ]

        self.page_states = []

        is_staff = self.is_staff
        can_change = self.can_change
        edit_mode = self.edit_mode

        if can_change:
            items.append(
                self.edit_mode_switcher
            )

        if is_staff:

            current_page = self.request.current_page

            if current_page:
                states = current_page.last_page_states()
                has_states = bool(len(states))
                self.page_states = states
                if has_states:
                    items.append(
                        TemplateHTML(LEFT, 'status',
                                     'cms/toolbar/items/status.html')
                    )

                # publish button
                if edit_mode:
                    if current_page.has_publish_permission(self.request):
                        items.append(
                            GetButton(RIGHT, 'moderator', _("Publish"), _get_publish_url)
                        )
                    if self.revert_button.is_enabled_for(self.request):
                        items.append(self.revert_button)

                # The 'templates' Menu
                if can_change:
                    items.append(self.get_template_menu(context, can_change, is_staff))

                # The 'page' Menu
                items.append(self.get_page_menu(context, can_change, is_staff))

            # The 'Admin' Menu
            items.append(self.get_admin_menu(context, can_change, is_staff))

        if not self.request.user.is_authenticated():
            items.append(
                TemplateHTML(LEFT, 'login', 'cms/toolbar/items/login.html')
            )
        else:
            items.append(
                GetButton(RIGHT, 'logout', _('Logout'), '?cms-toolbar-logout',
                    cms_static_url('images/toolbar/icons/icon_lock.png'))
            )
        return items

    def get_template_menu(self, context, can_change, is_staff):
        menu_items = []
        page = self.request.current_page.get_draft_object()
        url = reverse('admin:cms_page_change_template', args=(page.pk,))
        for path, name in settings.CMS_TEMPLATES:
            args = urllib.urlencode({'template': path})
            css = 'template'
            if page.get_template() == path:
                css += ' active'
            menu_items.append(
                ListItem(css, name, '%s?%s' % (url, args), 'POST'),
            )
        return List(RIGHT, 'templates', _('Template'),
                    '', items=menu_items)
    
    def get_page_menu(self, context, can_change, is_staff):
        """
        Builds the 'page menu'
        """
        menu_items = [
            ListItem('overview', _('Move/add Pages'),
                     reverse('admin:cms_page_changelist'),
                     icon=cms_static_url('images/toolbar/icons/icon_sitemap.png')),
        ]
        menu_items.append(
            ListItem('addchild', _('Add child page'),
                     _get_add_child_url,
                     icon=cms_static_url('images/toolbar/icons/icon_child.png'))
        )
        
        menu_items.append(
            ListItem('addsibling', _('Add sibling page'),
                     _get_add_sibling_url,
                     icon=cms_static_url('images/toolbar/icons/icon_sibling.png'))
        )
            
        menu_items.append(
            ListItem('delete', _('Delete Page'), _get_delete_url,
                     icon=cms_static_url('images/toolbar/icons/icon_delete.png'))
        )
        return List(RIGHT, 'page', _('Page'),
                    cms_static_url('images/toolbar/icons/icon_page.png'),
                    items=menu_items)
    
    def get_admin_menu(self, context, can_change, is_staff):
        """
        Builds the 'admin menu' (the one with the cogwheel)
        """
        admin_items = [
            ListItem('admin', _('Site Administration'),
                     reverse('admin:index'),
                     icon=cms_static_url('images/toolbar/icons/icon_admin.png')),
        ]
        if can_change and self.request.current_page:
            admin_items.append(
                ListItem('settings', _('Page Settings'),
                         _get_page_admin_url,
                         icon=cms_static_url('images/toolbar/icons/icon_page.png'))
            )
            if 'reversion' in settings.INSTALLED_APPS:
                admin_items.append(
                    ListItem('history', _('View History'),
                             _get_page_history_url,
                             icon=cms_static_url('images/toolbar/icons/icon_history.png'))
                )
        return List(RIGHT, 'admin', _('Admin'),
                    cms_static_url('images/toolbar/icons/icon_admin.png'),
                    items=admin_items)

