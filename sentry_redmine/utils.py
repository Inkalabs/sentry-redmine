from sentry.web.helpers import render_to_string
from sentry.utils.email import inline_css

import re


def clean_html(raw_html):
    clean_r = re.compile('@import.*')
    clean_text = re.sub(clean_r, '', raw_html)
    return clean_text


def render_html_body(context, html_template):
    html_body = render_to_string(html_template, context)
    clean_html_body = clean_html(html_body)
    return inline_css(clean_html_body)
