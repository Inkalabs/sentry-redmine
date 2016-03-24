from __future__ import absolute_import

from django.utils.translation import ugettext_lazy as _

from sentry.plugins.bases.issue import IssuePlugin
from sentry.utils.http import absolute_uri

from .client import RedmineClient
from .forms import RedmineOptionsForm, RedmineNewIssueForm


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
        return all((self.get_option(k, project) for k in ('host', 'key', 'project_id')))

    def get_new_issue_title(self, **kwargs):
        return 'Create Redmine Task'

    def get_initial_form_data(self, request, group, event, **kwargs):
        return {
            'description': self._get_group_description(request, group, event),
            'title': self._get_group_title(request, group, event),
        }

    def _get_group_description(self, request, group, event):
        output = [
            absolute_uri(group.get_absolute_url()),
        ]
        body = self._get_group_body(request, group, event)
        if body:
            output.extend([
                '',
                '<pre>',
                body,
                '</pre>',
            ])
        return '\n'.join(output)

    def get_client(self, project):
        return RedmineClient(
            host=self.get_option('host', project),
            key=self.get_option('key', project),
        )

    def create_issue(self, group, form_data, **kwargs):
        """
        Create a Redmine issue
        """
        client = self.get_client(group.project)
        default_priority = self.get_option('default_priority', group.project)
        if default_priority is None:
            default_priority = 4

        response = client.create_issue({
            'project_id': self.get_option('project_id', group.project),
            'tracker_id': self.get_option('tracker_id', group.project),
            'priority_id': default_priority,
            'subject': form_data['title'].encode('utf-8'),
            'description': form_data['description'].encode('utf-8'),
        })
        return response['issue']['id']

    def get_issue_url(self, group, issue_id, **kwargs):
        host = self.get_option('host', group.project)
        return '{}/issues/{}'.format(host.rstrip('/'), issue_id)
