from django import forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _, ugettext_lazy
from django.conf import settings
from cms.settings import CMS_LANGUAGES, CMS_UNIQUE_SLUGS, CMS_APPLICATIONS_URLS, CMS_FLAT_URLS
from cms.models import Page, Title
from cms.urlutils import any_path_re

class PageForm(forms.ModelForm):
    APPLICATION_URLS = (('', '----------'), ) + CMS_APPLICATIONS_URLS
    title = forms.CharField(label=_("Title"), widget=forms.TextInput(),
        help_text=_('The default title'))
    language = forms.ChoiceField(label=_("Language"), choices=CMS_LANGUAGES,
        help_text=_('The current language of the content fields.'))
    slug = forms.CharField(label=_("Slug"), widget=forms.TextInput(),
        help_text=_('The part of the title that is used in the url'))
    application_urls = forms.ChoiceField(label=_('Application'), 
        choices=APPLICATION_URLS, required=False,  
        help_text=_('Hook application to this page.'))
    overwrite_url = forms.CharField(label='Overwrite url', max_length=255, required=False,
        help_text=_('Keep this field empty if standard path should be used.'))
    
    class Meta:
        model = Page

    def clean_slug(self):
        slug = slugify(self.cleaned_data['slug'])
        page = self.instance
        lang = self.cleaned_data['language']
        parent = self.cleaned_data['parent']
        if CMS_UNIQUE_SLUGS:
            titles = Title.objects.filter(slug=slug)
        else:
            titles = Title.objects.filter(slug=slug, language=lang)        
        if not CMS_FLAT_URLS:
            titles = titles.filter(page__parent=parent)
        if self.instance.pk:
            titles = titles.exclude(language=lang, page=page)
        if titles.count():
            raise forms.ValidationError(ugettext_lazy('Another page with this slug already exists'))
        return slug
    
    def clean_reverse_id(self):
        id = self.cleaned_data['reverse_id']
        if id:
            if Page.objects.filter(reverse_id=id).exclude(pk=self.instance.pk).count():
                raise forms.ValidationError(ugettext_lazy('A page with this reverse url id exists already.'))
        return id

    def clean_overwrite_url(self):
        url = self.cleaned_data['overwrite_url']
        if url:
            if not any_path_re.match(url):
                raise forms.ValidationError(ugettext_lazy('Invalid url, use /my/url format.'))
        return url

