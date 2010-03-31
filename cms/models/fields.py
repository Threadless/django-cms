from cms.models.placeholdermodel import Placeholder
from cms.forms.widgets import PluginEditor
from cms.plugin_pool import plugin_pool
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.template.loader import render_to_string
from django.db import models
from django import forms
from cms.models.pagemodel import Page
from cms.forms.fields import PageSelectFormField


class PlaceholderPluginEditorWidget(PluginEditor):
    def render(self, name, value, attrs=None):
        try:
            ph = Placeholder.objects.get(pk=value)
        except Placeholder.DoesNotExist:
            ph = None
            context = {'add':True}
        if ph:
            context = {
                'plugin_list': ph.cmsplugin_set.all().order_by('position'),
                'installed_plugins': plugin_pool.get_all_plugins(ph.slot),
                'copy_languages': [], # TODO?
                'language': None, # TODO?
                'show_copy': False, # The copy function does not make sense on non-page objects
                'urloverride': True,
                'placeholder': ph,
            }
        return mark_safe(render_to_string(
            'admin/cms/page/widgets/plugin_editor.html', context))


class PlaceholderFormField(forms.Field):
    pass


class PlaceholderField(models.ForeignKey):
    def __init__(self, slotname, default_width=None, **kwargs):
        self.slotname = slotname
        self.default_width = default_width
        kwargs.update({'null':True}) # always allow Null
        super(PlaceholderField, self).__init__(Placeholder, **kwargs)
    
    def formfield(self, **kwargs):
        """
        Returns a django.forms.Field instance for this database Field.
        """
        defaults = {'label': capfirst(self.verbose_name), 'help_text': self.help_text}
        defaults.update(kwargs)
        widget = PlaceholderPluginEditorWidget()
        widget.choices = []
        return PlaceholderFormField(required=False, widget=widget, **defaults)
    
    def _get_new_placeholder(self):
        return Placeholder.objects.create(slot=self.slotname, default_width=self.default_width) 

    def pre_save(self, model_instance, add):
        if not model_instance.pk:
            setattr(model_instance, self.name, self._get_new_placeholder().pk)
        return super(PlaceholderField, self).pre_save(model_instance, add)

    def save_form_data(self, instance, data):
        if not instance.pk:
            data = self._get_new_placeholder()
        else:
            data = getattr(instance, self.name)
            if not isinstance(data, Placeholder):
                data = self._get_new_placeholder()
        super(PlaceholderField, self).save_form_data(instance, data)
    
    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect ourselves, since we inherit.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.related.ForeignKey"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)

class PageField(models.ForeignKey):
    default_form_class = PageSelectFormField
    default_model_class = Page
    def __init__(self, **kwargs):
        # we call ForeignKey.__init__ with the Page model as parameter...
        # a PageField can only be a ForeignKey to a Page
        super(PageField, self).__init__(self.default_model_class, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': self.default_form_class,
        }
        defaults.update(kwargs)
        return super(PageField, self).formfield(**defaults)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.related.ForeignKey"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)
