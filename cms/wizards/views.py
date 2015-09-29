# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

from django.forms import Form
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.template.response import SimpleTemplateResponse
from django.utils.translation import get_language_from_request

try:
    # This try/except block can be removed when we stop supporting Django 1.6
    from django.contrib.formtools.wizard.views import SessionWizardView
except ImportError:
    # This is fine from Django 1.7
    from formtools.wizard.views import SessionWizardView

from .wizard_pool import wizard_pool
from .forms import (
    WizardStep1Form,
    WizardStep2BaseForm,
    step2_form_factory,
)


class WizardViewMixin(object):
    language_code = None

    @transaction.atomic()
    def dispatch(self, request, *args, **kwargs):
        self.language_code = get_language_from_request(request, check_path=True)
        response = super(WizardViewMixin, self).dispatch(
            request, *args, **kwargs)
        return response

    def get_form_kwargs(self):
        kwargs = super(WizardViewMixin, self).get_form_kwargs()
        kwargs.update({'wizard_language': self.language_code})
        return kwargs


class WizardCreateView(WizardViewMixin, SessionWizardView):
    template_name = 'cms/wizards/start.html'
    file_storage = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, 'wizard_tmp_files'))

    form_list = [
        ('0', WizardStep1Form),
        # Form is used as a placeholder form.
        # the real form will be loaded after step 0
        ('1', Form),
    ]

    def is_first_step(self, step=None):
        step = step or self.steps.current
        return step == '0'

    def is_second_step(self, step=None):
        step = step or self.steps.current
        return step == '1'

    def get_form_initial(self, step):
        initial = super(WizardCreateView, self).get_form_initial(step)

        if self.is_first_step(step):
            # set the current page from GET param.
            initial['page'] = self.request.GET.get('page')
            # preselect a space if provided via GET param.
            initial['space'] = self.request.GET.get('space')
        return initial

    def get_context_data(self, **kwargs):
        context = super(WizardCreateView, self).get_context_data(**kwargs)

        if self.is_second_step():
            context['wizard_entry'] = self.get_selected_entry()
            context['inlineformset'] = context['form'].inlineformset
        return context

    def get_form_kwargs(self, step=None):
        kwargs = super(WizardCreateView, self).get_form_kwargs()
        kwargs['wizard_user'] = self.request.user

        if self.is_second_step(step):
            kwargs['wizard_page'] = self.get_origin_page()
        return kwargs

    def get_form(self, step=None, data=None, files=None):
        if step is None:
            step = self.steps.current

        if self.is_second_step(step):
            self.form_list[step] = self.get_step_2_form(step, data, files)
        return super(WizardCreateView, self).get_form(step, data, files)

    def get_step_2_form(self, step=None, data=None, files=None):
        entry_form_class = self.get_selected_entry().form
        step_2_base_form = self.get_step_2_base_form()

        inlineformset = self.get_inline_formset(
            data=data,
            files=files,
            prefix=self.get_form_prefix(step),
        )

        form = step2_form_factory(
            mixin_cls=step_2_base_form,
            entry_form_class=entry_form_class,
            attrs={'inlineformset': inlineformset}
        )
        return form

    def get_step_2_base_form(self):
        """
        Returns the base form to be used for step 2.
        This form is sub classed dynamically by the form defined per module.
        """
        return WizardStep2BaseForm

    def get_template_names(self):
        if self.is_first_step():
            template_name = self.template_name
        else:
            template_name = self.get_selected_entry().template_name
        return template_name

    def done(self, form_list, **kwargs):
        """
        This step only runs if all forms are valid. Simply emits a simple
        template that uses JS to redirect to the newly created object.
        """
        form_two = form_list[1]
        instance = form_two.save()

        context = {
            "url": self.get_success_url(instance),
        }

        return SimpleTemplateResponse("cms/wizards/done.html", context)

    def get_selected_entry(self):
        data = self.get_cleaned_data_for_step('0')
        return wizard_pool.get_entry(int(data['entry']))

    def get_origin_page(self):
        data = self.get_cleaned_data_for_step('0')
        return data.get('page')

    def get_success_url(self, instance):
        entry = self.get_selected_entry()
        success_url = entry.get_success_url(
            obj=instance,
            language=self.language_code
        )
        return success_url

    def get_inline_formset(self, **kwargs):
        entry = self.get_selected_entry()

        if entry.inlineformset:
            form_kwargs = self.get_form_kwargs(step='1')
            form_kwargs.update(kwargs)
            return entry.inlineformset(**form_kwargs)
        else:
            return None
