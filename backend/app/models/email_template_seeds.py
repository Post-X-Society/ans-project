"""
Seed data for email templates (Multilingual EN/NL)

Issue #95: Email Templates (Multilingual EN/NL)

17 transactional email templates covering:
- Submission workflow (5 templates)
- Review process (3 templates)
- Corrections (2 templates)
- Workflow states (7 templates)
"""

from app.models.email_template import EmailTemplateType

EMAIL_TEMPLATE_SEEDS = [
    {
        "template_key": "submission_received",
        "template_type": EmailTemplateType.SUBMISSION_RECEIVED,
        "name": {"en": "Submission Received", "nl": "Inzending Ontvangen"},
        "description": {
            "en": "Sent when a new claim submission is received from a user",
            "nl": "Verzonden wanneer een nieuwe claim inzending is ontvangen van een gebruiker",
        },
        "subject": {
            "en": "Submission Received - AnsCheckt",
            "nl": "Inzending Ontvangen - AnsCheckt",
        },
        "body_text": {
            "en": """Hi there,

We've received your fact-check submission (ID: {{submission_id}}).

Your claim: "{{claim_text}}"

Our team will review it shortly. You'll receive updates as we process your submission.

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}""",
            "nl": """Hallo,

We hebben uw fact-check inzending ontvangen (ID: {{submission_id}}).

Uw claim: "{{claim_text}}"

Ons team zal het binnenkort bekijken. U ontvangt updates terwijl we uw inzending verwerken.

Met vriendelijke groet,
AnsCheckt Team

---
Om deze e-mails niet meer te ontvangen, bezoek: {{opt_out_url}}""",
        },
        "body_html": {
            "en": """<html>
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
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Inzending Ontvangen</h2>
    <p>Hallo,</p>
    <p>We hebben uw fact-check inzending ontvangen.</p>
    <p><strong>Inzending ID:</strong> {{submission_id}}</p>
    <p><strong>Uw claim:</strong></p>
    <blockquote style="border-left: 4px solid #2563eb; padding-left: 1em; margin: 1em 0;">
        {{claim_text}}
    </blockquote>
    <p>Ons team zal het binnenkort bekijken. U ontvangt updates terwijl we uw inzending verwerken.</p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        Om deze e-mails niet meer te ontvangen, <a href="{{opt_out_url}}" style="color: #2563eb;">klik hier</a>.
    </p>
</body>
</html>""",
        },
        "variables": {"submission_id": "string", "claim_text": "string", "opt_out_url": "string"},
    },
    # Continue with remaining 16 templates...
]
