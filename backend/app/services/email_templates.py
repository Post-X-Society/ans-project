"""
Email templates for transactional notifications

Uses Jinja2 for template rendering with multilingual support
"""

import enum
from typing import Any

from jinja2 import Template


class EmailTemplate(str, enum.Enum):
    """Email template identifiers"""

    SUBMISSION_RECEIVED = "submission_received"
    WORKFLOW_UPDATE = "workflow_update"
    CORRECTION_REQUEST_RECEIVED = "correction_request_received"
    REVIEW_ASSIGNED = "review_assigned"
    FACT_CHECK_PUBLISHED = "fact_check_published"


# Email template definitions (subject, body_text, body_html)
TEMPLATES: dict[EmailTemplate, dict[str, str]] = {
    EmailTemplate.SUBMISSION_RECEIVED: {
        "subject": "Submission Received - AnsCheckt",
        "body_text": """Hi there,

We've received your fact-check submission (ID: {{submission_id}}).

Your claim: "{{claim_text}}"

Our team will review it shortly. You'll receive updates as we process your submission.

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}
""",
        "body_html": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Submission Received</h2>
    <p>Hi there,</p>
    <p>We've received your fact-check submission.</p>
    <p><strong>Submission ID:</strong> {{submission_id}}</p>
    <p><strong>Your claim:</strong></p>
    <blockquote style="border-left: 4px solid #2563eb; padding-left: 1em; margin: 1em 0;">
        {{claim_text}}
    </blockquote>
    <p>Our team will review it shortly. You'll receive updates as we process your submission.</p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        To stop receiving these emails, <a href="{{opt_out_url}}" style="color: #2563eb;">click here</a>.
    </p>
</body>
</html>
""",
    },
    EmailTemplate.WORKFLOW_UPDATE: {
        "subject": "Status Update: {{new_status}} - AnsCheckt",
        "body_text": """Hi there,

Your submission (ID: {{submission_id}}) status has been updated.

New status: {{new_status}}
{% if reviewer_name %}Reviewer: {{reviewer_name}}{% endif %}

{% if message %}
Message: {{message}}
{% endif %}

You can track your submission at: {{submission_url}}

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}
""",
        "body_html": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Status Update</h2>
    <p>Hi there,</p>
    <p>Your submission has been updated.</p>
    <p><strong>Submission ID:</strong> {{submission_id}}</p>
    <p><strong>New Status:</strong> <span style="color: #059669; font-weight: bold;">{{new_status}}</span></p>
    {% if reviewer_name %}
    <p><strong>Reviewer:</strong> {{reviewer_name}}</p>
    {% endif %}
    {% if message %}
    <p><strong>Message:</strong></p>
    <p style="background: #f3f4f6; padding: 1em; border-radius: 0.5em;">{{message}}</p>
    {% endif %}
    <p><a href="{{submission_url}}" style="color: #2563eb; text-decoration: none;">Track your submission</a></p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        To stop receiving these emails, <a href="{{opt_out_url}}" style="color: #2563eb;">click here</a>.
    </p>
</body>
</html>
""",
    },
    EmailTemplate.CORRECTION_REQUEST_RECEIVED: {
        "subject": "Correction Request Received - AnsCheckt",
        "body_text": """Hi there,

We've received your correction request for fact-check {{fact_check_id}}.

Our team will review your request and respond within 7 business days.

Request details: {{request_details}}

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}
""",
        "body_html": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Correction Request Received</h2>
    <p>Hi there,</p>
    <p>We've received your correction request for fact-check <strong>{{fact_check_id}}</strong>.</p>
    <p>Our team will review your request and respond within <strong>7 business days</strong>.</p>
    <p><strong>Request details:</strong></p>
    <p style="background: #f3f4f6; padding: 1em; border-radius: 0.5em;">{{request_details}}</p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        To stop receiving these emails, <a href="{{opt_out_url}}" style="color: #2563eb;">click here</a>.
    </p>
</body>
</html>
""",
    },
    EmailTemplate.REVIEW_ASSIGNED: {
        "subject": "New Review Assigned - AnsCheckt",
        "body_text": """Hi {{reviewer_name}},

You've been assigned a new submission to review.

Submission ID: {{submission_id}}
Claim: "{{claim_text}}"
Priority: {{priority}}

Review it here: {{review_url}}

Best regards,
AnsCheckt Team
""",
        "body_html": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">New Review Assigned</h2>
    <p>Hi <strong>{{reviewer_name}}</strong>,</p>
    <p>You've been assigned a new submission to review.</p>
    <p><strong>Submission ID:</strong> {{submission_id}}</p>
    <p><strong>Claim:</strong></p>
    <blockquote style="border-left: 4px solid #2563eb; padding-left: 1em; margin: 1em 0;">
        {{claim_text}}
    </blockquote>
    <p><strong>Priority:</strong> <span style="color: #dc2626;">{{priority}}</span></p>
    <p><a href="{{review_url}}" style="display: inline-block; background: #2563eb; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em; font-weight: bold;">Start Review</a></p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>
""",
    },
    EmailTemplate.FACT_CHECK_PUBLISHED: {
        "subject": "Fact-Check Published - AnsCheckt",
        "body_text": """Hi there,

The fact-check for your submission has been published!

Submission ID: {{submission_id}}
Rating: {{rating}}

View the full fact-check: {{fact_check_url}}

Thank you for helping us fight misinformation.

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}
""",
        "body_html": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #059669;">Fact-Check Published!</h2>
    <p>Hi there,</p>
    <p>The fact-check for your submission has been published.</p>
    <p><strong>Submission ID:</strong> {{submission_id}}</p>
    <p><strong>Rating:</strong> <span style="color: #dc2626; font-weight: bold;">{{rating}}</span></p>
    <p><a href="{{fact_check_url}}" style="display: inline-block; background: #059669; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em; font-weight: bold;">View Fact-Check</a></p>
    <p>Thank you for helping us fight misinformation.</p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        To stop receiving these emails, <a href="{{opt_out_url}}" style="color: #2563eb;">click here</a>.
    </p>
</body>
</html>
""",
    },
}


def render_template(template: EmailTemplate, context: dict[str, Any]) -> tuple[str, str, str]:
    """
    Render email template with context variables

    Args:
        template: Email template identifier
        context: Template variables as dictionary

    Returns:
        Tuple of (subject, body_text, body_html)

    Raises:
        ValueError: If template not found
    """
    if template not in TEMPLATES:
        raise ValueError(f"Template {template} not found")

    template_data: dict[str, str] = TEMPLATES[template]

    # Render subject
    subject_template: Template = Template(template_data["subject"])
    subject: str = subject_template.render(**context)

    # Render text body
    text_template: Template = Template(template_data["body_text"])
    body_text: str = text_template.render(**context)

    # Render HTML body
    html_template: Template = Template(template_data["body_html"])
    body_html: str = html_template.render(**context)

    return subject, body_text, body_html
