from __future__ import absolute_import
import json

import six
import re
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from sentry.plugins.bases import notify

from .client import RedmineClient
from .forms import RedmineOptionsForm
from .utils import render_html_body


class RedmineAutoTicketPlugin(notify.NotificationPlugin):
    title = 'Redmine Auto Ticket'
    slug = 'redmine_auto_ticket'
    conf_tilte = 'Redmine Auto Ticket'
    conf_key = 'redmine_auto_ticket'
    description = (
        'Create Automatically tickets in Redmine when a new issue appears'
    )
    author = 'Inkalabs'
    project_conf_form = RedmineOptionsForm

    def is_configured(self, project, **kwargs):
        return all((self.get_option(k, project) for k in ('host', 'key', 'project_id')))

    def notify(self, notification):
        event = notification.event
        group = event.group
        project = group.project
        org = group.organization

        if len(group.event_set) > 1 or not self.is_configured(event.project):
            return

        subject = event.get_email_subject()

        link = group.get_absolute_url()

        html_template = 'sentry/emails/error.html'

        rules = []
        for rule in notification.rules:
            rule_link = reverse(
                'sentry-edit-project-rule',
                args=[org.slug, project.slug, rule.id]
            )
            rules.append((rule.label, rule_link))

        enhanced_privacy = org.flags.enhanced_privacy

        context = {
            'project_label': project.get_full_name(),
            'group': group,
            'event': event,
            'link': link,
            'rules': rules,
            'enhanced_privacy': enhanced_privacy,
        }

        if not enhanced_privacy:
            interface_list = []
            for interface in six.itervalues(event.interfaces):
                body = interface.to_email_html(event)
                if not body:
                    continue
                text_body = interface.to_string(event)
                interface_list.append(
                    (interface.get_title(), mark_safe(body), text_body)
                )

            context.update({
                'tags': event.get_tags(),
                'interfaces': interface_list,
            })

        form_data = {
            'title': subject,
            'description': render_html_body(context, html_template)
        }
        self.create_issue(group, form_data)

    def create_issue(self, group, form_data, **kwargs):
        """
        Create a Redmine issue
        """

        client = self.get_client(group.project)
        default_priority = self.get_option('default_priority', group.project)
        if default_priority is None:
            default_priority = 4

        issue_dict = {
            'project_id': self.get_option('project_id', group.project),
            'tracker_id': self.get_option('tracker_id', group.project),
            'priority_id': default_priority,
            'subject': form_data['title'].encode('utf-8'),
            'description': form_data['description'].encode('utf-8'),
        }

        extra_fields_str = self.get_option('extra_fields', group.project)
        if extra_fields_str:
            extra_fields = json.loads(extra_fields_str)
        else:
            extra_fields = {}
        issue_dict.update(extra_fields)

        response = client.create_issue(issue_dict)
        return response['issue']['id']

    def get_client(self, project):
        return RedmineClient(
            host=self.get_option('host', project),
            key=self.get_option('key', project),
        )

NotifyConfigurationForm = RedmineOptionsForm
NotifyPlugin = RedmineAutoTicketPlugin
