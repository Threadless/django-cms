# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_permission_codename
from django.contrib.sites.models import Site

from cms.models import Page, GlobalPagePermission
from cms.utils import permissions

from .wizards.wizard_pool import wizard_pool
from .wizards.wizard_base import Wizard

from .forms.wizards import CreateCMSPageForm, CreateCMSSubPageForm


def user_has_page_add_permission(user, target, position=None, site=None):
    """
    Verify that «user» has permission to add a new page relative to «target».
    :param user: a User object
    :param target: a Page object
    :param position: a String "first-child", "last-child", "left", or "right"
    :param site: only used if target is None, a Site object
    :return:
    """
    if not user:
        return False
    if user.is_superuser:
        return True
    opts = Page._meta

    if target:
        if not Page.objects.filter(pk=target.pk).exists():
            return False

        global_add_perm = GlobalPagePermission.objects.user_has_add_permission(
            user, target.site).exists()
        perm_str = opts.app_label + '.' + get_permission_codename('add', opts)

        if user.has_perm(perm_str) and global_add_perm:
            return True
        if position in ("first-child", "last-child"):
            return permissions.has_generic_permission(
                target.pk, user, "add", target.site_id)
        elif position in ("left", "right") and target.parent_id:
            return permissions.has_generic_permission(
                target.parent_id, user, "add", target.site_id)
    else:
        if site is None:
            site = Site.objects.get_current()
        global_add_perm = GlobalPagePermission.objects.user_has_add_permission(
            user, site).exists()
        perm_str = opts.app_label + '.' + get_permission_codename('add', opts)
        if user.has_perm(perm_str) and global_add_perm:
            return True
    return False


class CMSPageWizard(Wizard):

    def user_has_add_permission(self, user, page=None, **kwargs):
        if not page:
            return False
        if not page.site_id:
            site = Site.objects.get_current()
        else:
            site = Site.objects.get(pk=page.site_id)
        return user_has_page_add_permission(
            user, page, position="right", site=site)


class CMSSubPageWizard(Wizard):

    def user_has_add_permission(self, user, page=None, **kwargs):
        if not page:
            return False
        if not page.site_id:
            site = Site.objects.get_current()
        else:
            site = Site.objects.get(pk=page.site_id)
        return user_has_page_add_permission(
            user, page, position="last-child", site=site)


cms_page_wizard = CMSPageWizard(
    title=_(u"New page"),
    weight=100,
    form=CreateCMSPageForm,
    model=Page,
    description=_(u"Create a new blank page as a sibling to the current page.")
)

cms_subpage_wizard = CMSSubPageWizard(
    title=_(u"New sub page"),
    weight=110,
    form=CreateCMSSubPageForm,
    model=Page,
    description=_(u"Create a sub-page to the current page.")
)

wizard_pool.register(cms_page_wizard)
wizard_pool.register(cms_subpage_wizard)
