from sentry.web.helpers import render_to_string
from sentry.utils.email import inline_css


def render_html_body(context, html_template):
    html_body = render_to_string(html_template, context)
    return inline_css(html_body)
