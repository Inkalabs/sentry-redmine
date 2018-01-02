from __future__ import absolute_import
import json

from django import forms
from django.utils.translation import ugettext_lazy as _
from sentry.plugins.bases import notify
from .client import RedmineClient


class RedmineOptionsForm(notify.NotificationConfigurationForm):
    host = forms.URLField(help_text=_("e.g. http://bugs.redmine.org"))
    key = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'span9'}),
        help_text='Your API key is available on your account page after enabling the Rest API (Administration -> Settings -> Authentication)')
    project_id = forms.IntegerField(
        label='Project')
    tracker_id = forms.IntegerField(
        label='Tracker')
    default_priority = forms.IntegerField(
        label='Default Priority')
    extra_fields = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'span9'}),
        help_text='Extra attributes (custom fields, status id, etc.) in JSON format',
        label='Extra Fields',
        required=False)

    def clean(self):
        cd = self.cleaned_data
        if cd.get('host') and cd.get('key'):
            client = RedmineClient(cd['host'], cd['key'])
            try:
                client.get_projects()
            except Exception:
                raise forms.ValidationError('There was an issue authenticating with Redmine')
        return cd

    def clean_host(self):
        """
        Strip forward slashes off any url passed through the form.
        """
        url = self.cleaned_data.get('host')
        if url:
            return url.rstrip('/')
        return url

    def clean_extra_fields(self):
        """
        Ensure that the value provided is either a valid JSON dictionary,
        or the empty string.
        """
        extra_fields_json = self.cleaned_data.get('extra_fields').strip()
        if not extra_fields_json:
            return ''

        try:
            extra_fields_dict = json.loads(extra_fields_json)
        except ValueError:
            raise forms.ValidationError('Invalid JSON specified')

        if not isinstance(extra_fields_dict, dict):
            raise forms.ValidationError('JSON dictionary must be specified')
        return json.dumps(extra_fields_dict, indent=4)


class RedmineNewIssueForm(forms.Form):
    title = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'span9'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'span9'}))
