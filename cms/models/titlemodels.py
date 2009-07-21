from datetime import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _
from publisher import Publisher
from cms import settings
from cms.models.managers import TitleManager
from cms.models.pagemodel import Page


class Title(Publisher):
    language = models.CharField(_("language"), max_length=5, db_index=True)
    title = models.CharField(_("title"), max_length=255)
    menu_title = models.CharField(_("title"), max_length=255, blank=True, null=True, help_text=_("overwrite the title in the menu"))
    slug = models.SlugField(_("slug"), max_length=255, db_index=True, unique=False)
    path = models.CharField(_("path"), max_length=255, db_index=True)
    has_url_overwrite = models.BooleanField(_("has url overwrite"), default=False, db_index=True, editable=False)
    application_urls = models.CharField(_('application'), max_length=200, choices=settings.CMS_APPLICATIONS_URLS, blank=True, null=True, db_index=True)
    redirect = models.CharField(_("redirect"), max_length=255, blank=True, null=True)
    meta_description = models.TextField(_("description"), max_length=255, blank=True, null=True)
    meta_keywords = models.CharField(_("keywords"), max_length=255, blank=True, null=True)
    page_title = models.CharField(_("title"), max_length=255, blank=True, null=True, help_text=_("overwrite the title (html title tag)"))
    page = models.ForeignKey(Page, verbose_name=_("page"), related_name="title_set")
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=datetime.now)
    
    objects = TitleManager()
    
    class Meta:
        unique_together = (('publisher_is_draft', 'language', 'page'),)
        app_label = 'cms'
    
    def __unicode__(self):
        return "%s (%s)" % (self.title, self.slug) 

    def save(self):
        # Build path from parent page's path and slug
        current_path = self.path
        parent_page = self.page.parent
        
        slug = u'%s' % self.slug
        if parent_page:
            self.path = u'%s/%s' % (Title.objects.get_title(parent_page, language=self.language, language_fallback=True).path, slug)
        else:
            self.path = u'%s' % slug
        super(Title, self).save()
        # Update descendants only if path changed
        if current_path != self.path:
            descendant_titles = Title.objects.filter(
                page__lft__gt=self.page.lft, 
                page__rght__lt=self.page.rght, 
                page__tree_id__exact=self.page.tree_id,
                language=self.language
            )
            for descendant_title in descendant_titles:
                descendant_title.path = descendant_title.path.replace(current_path, self.path, 1)
                descendant_title.save()

    @property
    def overwrite_url(self):
        """Return overrwriten url, or None
        """
        if self.has_url_overwrite:
            return self.path
        return None
        
        
class EmptyTitle(object):
    """Empty title object, can be returned from Page.get_title_obj() if required
    title object doesn't exists.
    """
    title = ""
    slug = ""
    path = ""
    meta_description = ""
    meta_keywords = ""
    redirect = ""
    has_url_overwite = False
    application_urls = ""
    menu_title = ""
    page_title = ""
    
    @property
    def overwrite_url(self):
        return None
    
    
if 'reversion' in settings.INSTALLED_APPS: 
    import reversion       
    reversion.register(Title)