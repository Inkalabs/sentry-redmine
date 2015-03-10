"""
sentry_redmine.plugin
~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2011 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from sentry import http
from sentry.utils import json
from sentry.plugins.bases.issue import IssuePlugin

import urlparse


class RedmineOptionsForm(forms.Form):
    host = forms.URLField(help_text=_("e.g. http://bugs.redmine.org"))
    key = forms.CharField(widget=forms.TextInput(attrs={'class': 'span9'}))
    project_id = forms.CharField(widget=forms.TextInput(attrs={'class': 'span9'}))
    tracker_id = forms.CharField(widget=forms.TextInput(attrs={'class': 'span9'}))

    def clean(self):
        config = self.cleaned_data
        if not all(config.get(k) for k in ('host', 'key', 'project_id', 'tracker_id')):
            raise forms.ValidationError('Missing required configuration value')
        return config


class RedmineNewIssueForm(forms.Form):
    title = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'span9'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'span9'}))


class RedminePlugin(IssuePlugin):
    author = 'Idea Device'
    author_url = 'https://github.com/ideadevice/sentry-redmine'
    version = '0.1.0'
    description = "Integrate Redmine issue tracking by linking a user account to a project."
    resource_links = [
        ('Bug Tracker', 'https://github.com/ideadevice/sentry-redmine/issues'),
        ('Source', 'https://github.com/ideadevice/sentry-redmine'),
    ]

    slug = 'redmine'
    title = _('Redmine')
    conf_title = 'Redmine'
    conf_key = 'redmine'
    project_conf_form = RedmineOptionsForm
    new_issue_form = RedmineNewIssueForm

    def is_configured(self, project, **kwargs):
        return all((self.get_option(k, project) for k in ('host', 'key', 'project_id', 'tracker_id')))

    def get_new_issue_title(self, **kwargs):
        return 'Create Redmine Task'

    def get_initial_form_data(self, request, group, event, **kwargs):
        return {
            'description': self._get_group_description(request, group, event),
            'title': 'Sentry:%s' % self._get_group_title(request, group, event),
        }

    def create_issue(self, group, form_data, **kwargs):
        """Create a Redmine issue"""
        headers = {
            "X-Redmine-API-Key": self.get_option('key', group.project),
            "Content-Type": "application/json",
        }
        url = urlparse.urljoin(self.get_option('host', group.project), "issues.json")
        payload = {
            'project_id': self.get_option('project_id', group.project),
            'tracker_id': self.get_option('tracker_id', group.project),
            'status_id': '0',
            'subject': form_data['title'].encode('utf-8'),
            'description': form_data['description'].encode('utf-8'),
        }

        session = http.build_session()
        r = session.post(url, data=json.dumps({'issue': payload}), headers=headers)
        data = json.loads(r.text)

        if 'issue' not in data or 'id' not in data['issue']:
            raise Exception('Unable to create redmine ticket')

        return data['issue']['id']

    def get_issue_url(self, group, issue_id, **kwargs):
        host = self.get_option('host', group.project)
        return urlparse.urljoin(host, '/issues/%s' % issue_id)
