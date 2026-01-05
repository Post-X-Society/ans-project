"""
Seed email templates into the database

Run with:
    python -m app.db.seed_email_templates
"""

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.email_template import EmailTemplateType
from app.services.email_template_service import EmailTemplateService

# Template data with full EN/NL content
TEMPLATES: list[dict[str, Any]] = [
    {
        "template_key": "submission_received",
        "template_type": EmailTemplateType.SUBMISSION_RECEIVED,
        "name": {"en": "Submission Received", "nl": "Inzending Ontvangen"},
        "description": {
            "en": "Sent when a new claim submission is received",
            "nl": "Verzonden wanneer een nieuwe claim is ontvangen",
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
        <a href="{{opt_out_url}}" style="color: #2563eb;">Unsubscribe from emails</a>
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
        <a href="{{opt_out_url}}" style="color: #2563eb;">Afmelden voor e-mails</a>
    </p>
</body>
</html>""",
        },
        "variables": {
            "submission_id": "string",
            "claim_text": "string",
            "opt_out_url": "string",
        },
    },
    {
        "template_key": "reviewer_assigned",
        "template_type": EmailTemplateType.REVIEWER_ASSIGNED,
        "name": {"en": "Reviewer Assigned", "nl": "Reviewer Toegewezen"},
        "description": {
            "en": "Sent when a reviewer is assigned to a submission",
            "nl": "Verzonden wanneer een reviewer wordt toegewezen aan een inzending",
        },
        "subject": {
            "en": "New Review Assignment - AnsCheckt",
            "nl": "Nieuwe Review Opdracht - AnsCheckt",
        },
        "body_text": {
            "en": """Hi {{reviewer_name}},

You've been assigned a new submission to review.

Submission ID: {{submission_id}}
Claim: "{{claim_text}}"
Priority: {{priority}}

Review it here: {{review_url}}

Best regards,
AnsCheckt Team""",
            "nl": """Hallo {{reviewer_name}},

U bent toegewezen aan een nieuwe inzending om te beoordelen.

Inzending ID: {{submission_id}}
Claim: "{{claim_text}}"
Prioriteit: {{priority}}

Beoordeel hier: {{review_url}}

Met vriendelijke groet,
AnsCheckt Team""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">New Review Assignment</h2>
    <p>Hi <strong>{{reviewer_name}}</strong>,</p>
    <p>You've been assigned a new submission to review.</p>
    <p><strong>Submission ID:</strong> {{submission_id}}</p>
    <p><strong>Claim:</strong></p>
    <blockquote style="border-left: 4px solid #2563eb; padding-left: 1em; margin: 1em 0;">
        {{claim_text}}
    </blockquote>
    <p><strong>Priority:</strong> <span style="color: #dc2626;">{{priority}}</span></p>
    <p><a href="{{review_url}}" style="display: inline-block; background: #2563eb; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Start Review</a></p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Nieuwe Review Opdracht</h2>
    <p>Hallo <strong>{{reviewer_name}}</strong>,</p>
    <p>U bent toegewezen aan een nieuwe inzending om te beoordelen.</p>
    <p><strong>Inzending ID:</strong> {{submission_id}}</p>
    <p><strong>Claim:</strong></p>
    <blockquote style="border-left: 4px solid #2563eb; padding-left: 1em; margin: 1em 0;">
        {{claim_text}}
    </blockquote>
    <p><strong>Prioriteit:</strong> <span style="color: #dc2626;">{{priority}}</span></p>
    <p><a href="{{review_url}}" style="display: inline-block; background: #2563eb; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Start Review</a></p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
        },
        "variables": {
            "reviewer_name": "string",
            "submission_id": "string",
            "claim_text": "string",
            "priority": "string",
            "review_url": "string",
        },
    },
    {
        "template_key": "workflow_update",
        "template_type": EmailTemplateType.WORKFLOW_UPDATE,
        "name": {"en": "Workflow Status Update", "nl": "Workflow Status Update"},
        "description": {
            "en": "Sent when submission workflow status changes",
            "nl": "Verzonden wanneer de workflow status van een inzending verandert",
        },
        "subject": {
            "en": "Status Update: {{claim_text}}",
            "nl": "Status Update: {{claim_text}}",
        },
        "body_text": {
            "en": """Hi there,

Your submission (ID: {{submission_id}}) has a status update.

New Status: {{new_status}}
{% if status_message %}Message: {{status_message}}{% endif %}

View details: {{submission_url}}

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}""",
            "nl": """Hallo,

Uw inzending (ID: {{submission_id}}) heeft een status update.

Nieuwe Status: {{new_status}}
{% if status_message %}Bericht: {{status_message}}{% endif %}

Bekijk details: {{submission_url}}

Met vriendelijke groet,
AnsCheckt Team

---
Om deze e-mails niet meer te ontvangen, bezoek: {{opt_out_url}}""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Status Update</h2>
    <p>Hi there,</p>
    <p>Your submission has a status update.</p>
    <p><strong>Submission ID:</strong> {{submission_id}}</p>
    <p><strong>New Status:</strong> <span style="background: #dbeafe; padding: 0.25em 0.5em; border-radius: 0.25em;">{{new_status}}</span></p>
    {% if status_message %}<p><strong>Message:</strong> {{status_message}}</p>{% endif %}
    <p><a href="{{submission_url}}" style="color: #2563eb;">View Submission</a></p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Unsubscribe from emails</a>
    </p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Status Update</h2>
    <p>Hallo,</p>
    <p>Uw inzending heeft een status update.</p>
    <p><strong>Inzending ID:</strong> {{submission_id}}</p>
    <p><strong>Nieuwe Status:</strong> <span style="background: #dbeafe; padding: 0.25em 0.5em; border-radius: 0.25em;">{{new_status}}</span></p>
    {% if status_message %}<p><strong>Bericht:</strong> {{status_message}}</p>{% endif %}
    <p><a href="{{submission_url}}" style="color: #2563eb;">Bekijk Inzending</a></p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Afmelden voor e-mails</a>
    </p>
</body>
</html>""",
        },
        "variables": {
            "submission_id": "string",
            "claim_text": "string",
            "new_status": "string",
            "status_message": "string (optional)",
            "submission_url": "string",
            "opt_out_url": "string",
        },
    },
    {
        "template_key": "correction_request_received",
        "template_type": EmailTemplateType.CORRECTION_REQUEST_RECEIVED,
        "name": {"en": "Correction Request Received", "nl": "Correctieverzoek Ontvangen"},
        "description": {
            "en": "Sent when a correction request is submitted",
            "nl": "Verzonden wanneer een correctieverzoek wordt ingediend",
        },
        "subject": {
            "en": "Correction Request Received - AnsCheckt",
            "nl": "Correctieverzoek Ontvangen - AnsCheckt",
        },
        "body_text": {
            "en": """Hi there,

We've received your correction request for:
Fact-check: {{fact_check_title}}

Your correction details:
{{correction_text}}

Our team will review your request and respond within 3-5 business days.

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}""",
            "nl": """Hallo,

We hebben uw correctieverzoek ontvangen voor:
Fact-check: {{fact_check_title}}

Uw correctie details:
{{correction_text}}

Ons team zal uw verzoek beoordelen en binnen 3-5 werkdagen reageren.

Met vriendelijke groet,
AnsCheckt Team

---
Om deze e-mails niet meer te ontvangen, bezoek: {{opt_out_url}}""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Correction Request Received</h2>
    <p>Hi there,</p>
    <p>We've received your correction request for:</p>
    <p><strong>Fact-check:</strong> {{fact_check_title}}</p>
    <p><strong>Your correction:</strong></p>
    <blockquote style="border-left: 4px solid #f59e0b; padding-left: 1em; margin: 1em 0; background: #fffbeb; padding: 1em;">
        {{correction_text}}
    </blockquote>
    <p>Our team will review your request and respond within 3-5 business days.</p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Unsubscribe from emails</a>
    </p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Correctieverzoek Ontvangen</h2>
    <p>Hallo,</p>
    <p>We hebben uw correctieverzoek ontvangen voor:</p>
    <p><strong>Fact-check:</strong> {{fact_check_title}}</p>
    <p><strong>Uw correctie:</strong></p>
    <blockquote style="border-left: 4px solid #f59e0b; padding-left: 1em; margin: 1em 0; background: #fffbeb; padding: 1em;">
        {{correction_text}}
    </blockquote>
    <p>Ons team zal uw verzoek beoordelen en binnen 3-5 werkdagen reageren.</p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Afmelden voor e-mails</a>
    </p>
</body>
</html>""",
        },
        "variables": {
            "fact_check_title": "string",
            "correction_text": "string",
            "opt_out_url": "string",
        },
    },
    {
        "template_key": "correction_approved",
        "template_type": EmailTemplateType.CORRECTION_APPROVED,
        "name": {"en": "Correction Approved", "nl": "Correctie Goedgekeurd"},
        "description": {
            "en": "Sent when a correction request is approved",
            "nl": "Verzonden wanneer een correctieverzoek wordt goedgekeurd",
        },
        "subject": {
            "en": "Your Correction Has Been Approved - AnsCheckt",
            "nl": "Uw Correctie Is Goedgekeurd - AnsCheckt",
        },
        "body_text": {
            "en": """Hi there,

Great news! Your correction request has been approved and published.

Fact-check: {{fact_check_title}}
View the updated fact-check: {{fact_check_url}}

Thank you for helping us maintain accuracy!

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}""",
            "nl": """Hallo,

Goed nieuws! Uw correctieverzoek is goedgekeurd en gepubliceerd.

Fact-check: {{fact_check_title}}
Bekijk de bijgewerkte fact-check: {{fact_check_url}}

Bedankt voor uw hulp bij het behouden van nauwkeurigheid!

Met vriendelijke groet,
AnsCheckt Team

---
Om deze e-mails niet meer te ontvangen, bezoek: {{opt_out_url}}""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #10b981;">✓ Correction Approved</h2>
    <p>Hi there,</p>
    <p>Great news! Your correction request has been approved and published.</p>
    <p><strong>Fact-check:</strong> {{fact_check_title}}</p>
    <p><a href="{{fact_check_url}}" style="display: inline-block; background: #10b981; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">View Updated Fact-Check</a></p>
    <p>Thank you for helping us maintain accuracy!</p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Unsubscribe from emails</a>
    </p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #10b981;">✓ Correctie Goedgekeurd</h2>
    <p>Hallo,</p>
    <p>Goed nieuws! Uw correctieverzoek is goedgekeurd en gepubliceerd.</p>
    <p><strong>Fact-check:</strong> {{fact_check_title}}</p>
    <p><a href="{{fact_check_url}}" style="display: inline-block; background: #10b981; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Bekijk Bijgewerkte Fact-Check</a></p>
    <p>Bedankt voor uw hulp bij het behouden van nauwkeurigheid!</p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Afmelden voor e-mails</a>
    </p>
</body>
</html>""",
        },
        "variables": {
            "fact_check_title": "string",
            "fact_check_url": "string",
            "opt_out_url": "string",
        },
    },
    {
        "template_key": "correction_rejected",
        "template_type": EmailTemplateType.CORRECTION_REJECTED,
        "name": {"en": "Correction Rejected", "nl": "Correctie Afgewezen"},
        "description": {
            "en": "Sent when a correction request is rejected",
            "nl": "Verzonden wanneer een correctieverzoek wordt afgewezen",
        },
        "subject": {
            "en": "Update on Your Correction Request - AnsCheckt",
            "nl": "Update over Uw Correctieverzoek - AnsCheckt",
        },
        "body_text": {
            "en": """Hi there,

Thank you for submitting a correction request for:
Fact-check: {{fact_check_title}}

After careful review, we've decided not to make changes at this time.

Reason: {{rejection_reason}}

If you have additional information or evidence, please feel free to submit a new request.

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}""",
            "nl": """Hallo,

Bedankt voor het indienen van een correctieverzoek voor:
Fact-check: {{fact_check_title}}

Na zorgvuldige beoordeling hebben we besloten op dit moment geen wijzigingen aan te brengen.

Reden: {{rejection_reason}}

Als u aanvullende informatie of bewijs heeft, dien dan gerust een nieuw verzoek in.

Met vriendelijke groet,
AnsCheckt Team

---
Om deze e-mails niet meer te ontvangen, bezoek: {{opt_out_url}}""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #6b7280;">Update on Your Correction Request</h2>
    <p>Hi there,</p>
    <p>Thank you for submitting a correction request for:</p>
    <p><strong>Fact-check:</strong> {{fact_check_title}}</p>
    <p>After careful review, we've decided not to make changes at this time.</p>
    <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 1em; margin: 1em 0;">
        <p style="margin: 0;"><strong>Reason:</strong> {{rejection_reason}}</p>
    </div>
    <p>If you have additional information or evidence, please feel free to submit a new request.</p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Unsubscribe from emails</a>
    </p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #6b7280;">Update over Uw Correctieverzoek</h2>
    <p>Hallo,</p>
    <p>Bedankt voor het indienen van een correctieverzoek voor:</p>
    <p><strong>Fact-check:</strong> {{fact_check_title}}</p>
    <p>Na zorgvuldige beoordeling hebben we besloten op dit moment geen wijzigingen aan te brengen.</p>
    <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 1em; margin: 1em 0;">
        <p style="margin: 0;"><strong>Reden:</strong> {{rejection_reason}}</p>
    </div>
    <p>Als u aanvullende informatie of bewijs heeft, dien dan gerust een nieuw verzoek in.</p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Afmelden voor e-mails</a>
    </p>
</body>
</html>""",
        },
        "variables": {
            "fact_check_title": "string",
            "rejection_reason": "string",
            "opt_out_url": "string",
        },
    },
    {
        "template_key": "review_assigned",
        "template_type": EmailTemplateType.REVIEW_ASSIGNED,
        "name": {"en": "Review Assigned", "nl": "Review Toegewezen"},
        "description": {
            "en": "Sent when a fact-check review is assigned",
            "nl": "Verzonden wanneer een fact-check review wordt toegewezen",
        },
        "subject": {
            "en": "Review Assignment - AnsCheckt",
            "nl": "Review Opdracht - AnsCheckt",
        },
        "body_text": {
            "en": """Hi {{reviewer_name}},

You've been assigned to review a fact-check.

Submission ID: {{submission_id}}
Claim: "{{claim_text}}"
Due Date: {{due_date}}

Please complete your review by the due date.
Review here: {{review_url}}

Best regards,
AnsCheckt Team""",
            "nl": """Hallo {{reviewer_name}},

U bent toegewezen om een fact-check te beoordelen.

Inzending ID: {{submission_id}}
Claim: "{{claim_text}}"
Deadline: {{due_date}}

Voltooi uw beoordeling voor de deadline.
Beoordeel hier: {{review_url}}

Met vriendelijke groet,
AnsCheckt Team""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Review Assignment</h2>
    <p>Hi <strong>{{reviewer_name}}</strong>,</p>
    <p>You've been assigned to review a fact-check.</p>
    <p><strong>Submission ID:</strong> {{submission_id}}</p>
    <p><strong>Claim:</strong></p>
    <blockquote style="border-left: 4px solid #2563eb; padding-left: 1em; margin: 1em 0;">
        {{claim_text}}
    </blockquote>
    <p><strong>Due Date:</strong> {{due_date}}</p>
    <p><a href="{{review_url}}" style="display: inline-block; background: #2563eb; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Start Review</a></p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Review Opdracht</h2>
    <p>Hallo <strong>{{reviewer_name}}</strong>,</p>
    <p>U bent toegewezen om een fact-check te beoordelen.</p>
    <p><strong>Inzending ID:</strong> {{submission_id}}</p>
    <p><strong>Claim:</strong></p>
    <blockquote style="border-left: 4px solid #2563eb; padding-left: 1em; margin: 1em 0;">
        {{claim_text}}
    </blockquote>
    <p><strong>Deadline:</strong> {{due_date}}</p>
    <p><a href="{{review_url}}" style="display: inline-block; background: #2563eb; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Start Review</a></p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
        },
        "variables": {
            "reviewer_name": "string",
            "submission_id": "string",
            "claim_text": "string",
            "due_date": "string",
            "review_url": "string",
        },
    },
    {
        "template_key": "review_completed",
        "template_type": EmailTemplateType.REVIEW_COMPLETED,
        "name": {"en": "Review Completed", "nl": "Review Voltooid"},
        "description": {
            "en": "Sent when a review is completed",
            "nl": "Verzonden wanneer een review is voltooid",
        },
        "subject": {
            "en": "Review Completed: {{claim_text}}",
            "nl": "Review Voltooid: {{claim_text}}",
        },
        "body_text": {
            "en": """Hi there,

The review of your submission (ID: {{submission_id}}) has been completed.

Verdict: {{verdict}}
{% if reviewer_notes %}Notes: {{reviewer_notes}}{% endif %}

View the full review: {{submission_url}}

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}""",
            "nl": """Hallo,

De beoordeling van uw inzending (ID: {{submission_id}}) is voltooid.

Oordeel: {{verdict}}
{% if reviewer_notes %}Notities: {{reviewer_notes}}{% endif %}

Bekijk de volledige beoordeling: {{submission_url}}

Met vriendelijke groet,
AnsCheckt Team

---
Om deze e-mails niet meer te ontvangen, bezoek: {{opt_out_url}}""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Review Completed</h2>
    <p>Hi there,</p>
    <p>The review of your submission has been completed.</p>
    <p><strong>Submission ID:</strong> {{submission_id}}</p>
    <p><strong>Verdict:</strong> <span style="background: #dbeafe; padding: 0.25em 0.5em; border-radius: 0.25em; font-weight: bold;">{{verdict}}</span></p>
    {% if reviewer_notes %}
    <div style="background: #f9fafb; border-left: 4px solid #6b7280; padding: 1em; margin: 1em 0;">
        <p style="margin: 0;"><strong>Reviewer Notes:</strong></p>
        <p style="margin: 0.5em 0 0 0;">{{reviewer_notes}}</p>
    </div>
    {% endif %}
    <p><a href="{{submission_url}}" style="color: #2563eb;">View Full Review</a></p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Unsubscribe from emails</a>
    </p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Review Voltooid</h2>
    <p>Hallo,</p>
    <p>De beoordeling van uw inzending is voltooid.</p>
    <p><strong>Inzending ID:</strong> {{submission_id}}</p>
    <p><strong>Oordeel:</strong> <span style="background: #dbeafe; padding: 0.25em 0.5em; border-radius: 0.25em; font-weight: bold;">{{verdict}}</span></p>
    {% if reviewer_notes %}
    <div style="background: #f9fafb; border-left: 4px solid #6b7280; padding: 1em; margin: 1em 0;">
        <p style="margin: 0;"><strong>Reviewer Notities:</strong></p>
        <p style="margin: 0.5em 0 0 0;">{{reviewer_notes}}</p>
    </div>
    {% endif %}
    <p><a href="{{submission_url}}" style="color: #2563eb;">Bekijk Volledige Beoordeling</a></p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Afmelden voor e-mails</a>
    </p>
</body>
</html>""",
        },
        "variables": {
            "submission_id": "string",
            "claim_text": "string",
            "verdict": "string",
            "reviewer_notes": "string (optional)",
            "submission_url": "string",
            "opt_out_url": "string",
        },
    },
    {
        "template_key": "fact_check_published",
        "template_type": EmailTemplateType.FACT_CHECK_PUBLISHED,
        "name": {"en": "Fact-Check Published", "nl": "Fact-Check Gepubliceerd"},
        "description": {
            "en": "Sent when a fact-check is published",
            "nl": "Verzonden wanneer een fact-check wordt gepubliceerd",
        },
        "subject": {
            "en": "Your Fact-Check is Now Live - AnsCheckt",
            "nl": "Uw Fact-Check is Nu Live - AnsCheckt",
        },
        "body_text": {
            "en": """Hi there,

Great news! Your fact-check submission has been published.

Claim: "{{claim_text}}"
Verdict: {{verdict}}

View the published fact-check: {{fact_check_url}}

Thank you for contributing to AnsCheckt!

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}""",
            "nl": """Hallo,

Goed nieuws! Uw fact-check inzending is gepubliceerd.

Claim: "{{claim_text}}"
Oordeel: {{verdict}}

Bekijk de gepubliceerde fact-check: {{fact_check_url}}

Bedankt voor uw bijdrage aan AnsCheckt!

Met vriendelijke groet,
AnsCheckt Team

---
Om deze e-mails niet meer te ontvangen, bezoek: {{opt_out_url}}""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #10b981;">🎉 Your Fact-Check is Now Live!</h2>
    <p>Hi there,</p>
    <p>Great news! Your fact-check submission has been published.</p>
    <p><strong>Claim:</strong></p>
    <blockquote style="border-left: 4px solid #10b981; padding-left: 1em; margin: 1em 0;">
        {{claim_text}}
    </blockquote>
    <p><strong>Verdict:</strong> <span style="background: #d1fae5; color: #065f46; padding: 0.25em 0.5em; border-radius: 0.25em; font-weight: bold;">{{verdict}}</span></p>
    <p><a href="{{fact_check_url}}" style="display: inline-block; background: #10b981; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">View Published Fact-Check</a></p>
    <p>Thank you for contributing to AnsCheckt!</p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Unsubscribe from emails</a>
    </p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #10b981;">🎉 Uw Fact-Check is Nu Live!</h2>
    <p>Hallo,</p>
    <p>Goed nieuws! Uw fact-check inzending is gepubliceerd.</p>
    <p><strong>Claim:</strong></p>
    <blockquote style="border-left: 4px solid #10b981; padding-left: 1em; margin: 1em 0;">
        {{claim_text}}
    </blockquote>
    <p><strong>Oordeel:</strong> <span style="background: #d1fae5; color: #065f46; padding: 0.25em 0.5em; border-radius: 0.25em; font-weight: bold;">{{verdict}}</span></p>
    <p><a href="{{fact_check_url}}" style="display: inline-block; background: #10b981; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Bekijk Gepubliceerde Fact-Check</a></p>
    <p>Bedankt voor uw bijdrage aan AnsCheckt!</p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Afmelden voor e-mails</a>
    </p>
</body>
</html>""",
        },
        "variables": {
            "claim_text": "string",
            "verdict": "string",
            "fact_check_url": "string",
            "opt_out_url": "string",
        },
    },
    {
        "template_key": "peer_review_request",
        "template_type": EmailTemplateType.PEER_REVIEW_REQUEST,
        "name": {"en": "Peer Review Request", "nl": "Peer Review Verzoek"},
        "description": {
            "en": "Sent when peer review is requested",
            "nl": "Verzonden wanneer peer review wordt aangevraagd",
        },
        "subject": {
            "en": "Peer Review Request - AnsCheckt",
            "nl": "Peer Review Verzoek - AnsCheckt",
        },
        "body_text": {
            "en": """Hi {{reviewer_name}},

You've been requested to provide a peer review for a fact-check.

Fact-Check: {{fact_check_title}}
Original Reviewer: {{original_reviewer}}
Requested By: {{requested_by}}

Please review the fact-check and provide your feedback.
Review here: {{review_url}}

Best regards,
AnsCheckt Team""",
            "nl": """Hallo {{reviewer_name}},

U wordt gevraagd om een peer review te geven voor een fact-check.

Fact-Check: {{fact_check_title}}
Originele Reviewer: {{original_reviewer}}
Aangevraagd Door: {{requested_by}}

Beoordeel de fact-check en geef uw feedback.
Beoordeel hier: {{review_url}}

Met vriendelijke groet,
AnsCheckt Team""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #8b5cf6;">Peer Review Request</h2>
    <p>Hi <strong>{{reviewer_name}}</strong>,</p>
    <p>You've been requested to provide a peer review for a fact-check.</p>
    <p><strong>Fact-Check:</strong> {{fact_check_title}}</p>
    <p><strong>Original Reviewer:</strong> {{original_reviewer}}</p>
    <p><strong>Requested By:</strong> {{requested_by}}</p>
    <p><a href="{{review_url}}" style="display: inline-block; background: #8b5cf6; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Start Peer Review</a></p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #8b5cf6;">Peer Review Verzoek</h2>
    <p>Hallo <strong>{{reviewer_name}}</strong>,</p>
    <p>U wordt gevraagd om een peer review te geven voor een fact-check.</p>
    <p><strong>Fact-Check:</strong> {{fact_check_title}}</p>
    <p><strong>Originele Reviewer:</strong> {{original_reviewer}}</p>
    <p><strong>Aangevraagd Door:</strong> {{requested_by}}</p>
    <p><a href="{{review_url}}" style="display: inline-block; background: #8b5cf6; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Start Peer Review</a></p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
        },
        "variables": {
            "reviewer_name": "string",
            "fact_check_title": "string",
            "original_reviewer": "string",
            "requested_by": "string",
            "review_url": "string",
        },
    },
    {
        "template_key": "peer_review_completed",
        "template_type": EmailTemplateType.PEER_REVIEW_COMPLETED,
        "name": {"en": "Peer Review Completed", "nl": "Peer Review Voltooid"},
        "description": {
            "en": "Sent when peer review is completed",
            "nl": "Verzonden wanneer peer review is voltooid",
        },
        "subject": {
            "en": "Peer Review Completed: {{fact_check_title}}",
            "nl": "Peer Review Voltooid: {{fact_check_title}}",
        },
        "body_text": {
            "en": """Hi {{original_reviewer}},

A peer review has been completed for your fact-check.

Fact-Check: {{fact_check_title}}
Peer Reviewer: {{peer_reviewer}}

View the peer review feedback: {{review_url}}

Best regards,
AnsCheckt Team""",
            "nl": """Hallo {{original_reviewer}},

Een peer review is voltooid voor uw fact-check.

Fact-Check: {{fact_check_title}}
Peer Reviewer: {{peer_reviewer}}

Bekijk de peer review feedback: {{review_url}}

Met vriendelijke groet,
AnsCheckt Team""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #8b5cf6;">Peer Review Completed</h2>
    <p>Hi <strong>{{original_reviewer}}</strong>,</p>
    <p>A peer review has been completed for your fact-check.</p>
    <p><strong>Fact-Check:</strong> {{fact_check_title}}</p>
    <p><strong>Peer Reviewer:</strong> {{peer_reviewer}}</p>
    <p><a href="{{review_url}}" style="color: #8b5cf6; font-weight: bold;">View Peer Review Feedback</a></p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #8b5cf6;">Peer Review Voltooid</h2>
    <p>Hallo <strong>{{original_reviewer}}</strong>,</p>
    <p>Een peer review is voltooid voor uw fact-check.</p>
    <p><strong>Fact-Check:</strong> {{fact_check_title}}</p>
    <p><strong>Peer Reviewer:</strong> {{peer_reviewer}}</p>
    <p><a href="{{review_url}}" style="color: #8b5cf6; font-weight: bold;">Bekijk Peer Review Feedback</a></p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
        },
        "variables": {
            "original_reviewer": "string",
            "fact_check_title": "string",
            "peer_reviewer": "string",
            "review_url": "string",
        },
    },
    {
        "template_key": "draft_reminder",
        "template_type": EmailTemplateType.DRAFT_REMINDER,
        "name": {"en": "Draft Reminder", "nl": "Concept Herinnering"},
        "description": {
            "en": "Sent as reminder for incomplete drafts",
            "nl": "Verzonden als herinnering voor onvolledige concepten",
        },
        "subject": {
            "en": "Reminder: Complete Your Fact-Check Draft - AnsCheckt",
            "nl": "Herinnering: Voltooi Uw Fact-Check Concept - AnsCheckt",
        },
        "body_text": {
            "en": """Hi {{reviewer_name}},

This is a friendly reminder about your incomplete fact-check draft.

Draft ID: {{draft_id}}
Claim: "{{claim_text}}"
Created: {{created_date}}

Please complete your draft when you have time.
Continue here: {{draft_url}}

Best regards,
AnsCheckt Team""",
            "nl": """Hallo {{reviewer_name}},

Dit is een vriendelijke herinnering over uw onvolledige fact-check concept.

Concept ID: {{draft_id}}
Claim: "{{claim_text}}"
Aangemaakt: {{created_date}}

Voltooi uw concept wanneer u tijd heeft.
Ga verder hier: {{draft_url}}

Met vriendelijke groet,
AnsCheckt Team""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #f59e0b;">⏰ Draft Reminder</h2>
    <p>Hi <strong>{{reviewer_name}}</strong>,</p>
    <p>This is a friendly reminder about your incomplete fact-check draft.</p>
    <p><strong>Draft ID:</strong> {{draft_id}}</p>
    <p><strong>Claim:</strong></p>
    <blockquote style="border-left: 4px solid #f59e0b; padding-left: 1em; margin: 1em 0;">
        {{claim_text}}
    </blockquote>
    <p><strong>Created:</strong> {{created_date}}</p>
    <p><a href="{{draft_url}}" style="display: inline-block; background: #f59e0b; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Continue Draft</a></p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #f59e0b;">⏰ Concept Herinnering</h2>
    <p>Hallo <strong>{{reviewer_name}}</strong>,</p>
    <p>Dit is een vriendelijke herinnering over uw onvolledige fact-check concept.</p>
    <p><strong>Concept ID:</strong> {{draft_id}}</p>
    <p><strong>Claim:</strong></p>
    <blockquote style="border-left: 4px solid #f59e0b; padding-left: 1em; margin: 1em 0;">
        {{claim_text}}
    </blockquote>
    <p><strong>Aangemaakt:</strong> {{created_date}}</p>
    <p><a href="{{draft_url}}" style="display: inline-block; background: #f59e0b; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Ga Verder met Concept</a></p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
        },
        "variables": {
            "reviewer_name": "string",
            "draft_id": "string",
            "claim_text": "string",
            "created_date": "string",
            "draft_url": "string",
        },
    },
    {
        "template_key": "system_notification",
        "template_type": EmailTemplateType.SYSTEM_NOTIFICATION,
        "name": {"en": "System Notification", "nl": "Systeem Notificatie"},
        "description": {
            "en": "Generic system notification template",
            "nl": "Algemeen systeem notificatie template",
        },
        "subject": {
            "en": "{{notification_title}} - AnsCheckt",
            "nl": "{{notification_title}} - AnsCheckt",
        },
        "body_text": {
            "en": """Hi {{user_name}},

{{notification_message}}

{% if action_url %}Take action: {{action_url}}{% endif %}

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}""",
            "nl": """Hallo {{user_name}},

{{notification_message}}

{% if action_url %}Actie ondernemen: {{action_url}}{% endif %}

Met vriendelijke groet,
AnsCheckt Team

---
Om deze e-mails niet meer te ontvangen, bezoek: {{opt_out_url}}""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">{{notification_title}}</h2>
    <p>Hi <strong>{{user_name}}</strong>,</p>
    <div style="background: #f9fafb; border-left: 4px solid #2563eb; padding: 1em; margin: 1em 0;">
        {{notification_message}}
    </div>
    {% if action_url %}
    <p><a href="{{action_url}}" style="display: inline-block; background: #2563eb; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Take Action</a></p>
    {% endif %}
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Unsubscribe from emails</a>
    </p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">{{notification_title}}</h2>
    <p>Hallo <strong>{{user_name}}</strong>,</p>
    <div style="background: #f9fafb; border-left: 4px solid #2563eb; padding: 1em; margin: 1em 0;">
        {{notification_message}}
    </div>
    {% if action_url %}
    <p><a href="{{action_url}}" style="display: inline-block; background: #2563eb; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Actie Ondernemen</a></p>
    {% endif %}
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Afmelden voor e-mails</a>
    </p>
</body>
</html>""",
        },
        "variables": {
            "user_name": "string",
            "notification_title": "string",
            "notification_message": "string",
            "action_url": "string (optional)",
            "opt_out_url": "string",
        },
    },
    {
        "template_key": "weekly_digest",
        "template_type": EmailTemplateType.WEEKLY_DIGEST,
        "name": {"en": "Weekly Digest", "nl": "Wekelijkse Samenvatting"},
        "description": {
            "en": "Weekly summary of activity and updates",
            "nl": "Wekelijkse samenvatting van activiteit en updates",
        },
        "subject": {
            "en": "Your Weekly AnsCheckt Digest",
            "nl": "Uw Wekelijkse AnsCheckt Samenvatting",
        },
        "body_text": {
            "en": """Hi {{user_name}},

Here's your weekly summary of AnsCheckt activity:

Submissions This Week: {{submission_count}}
Reviews Completed: {{review_count}}
Fact-Checks Published: {{published_count}}

{% if top_fact_checks %}
Top Fact-Checks This Week:
{{top_fact_checks}}
{% endif %}

View your dashboard: {{dashboard_url}}

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}""",
            "nl": """Hallo {{user_name}},

Hier is uw wekelijkse samenvatting van AnsCheckt activiteit:

Inzendingen Deze Week: {{submission_count}}
Reviews Voltooid: {{review_count}}
Fact-Checks Gepubliceerd: {{published_count}}

{% if top_fact_checks %}
Top Fact-Checks Deze Week:
{{top_fact_checks}}
{% endif %}

Bekijk uw dashboard: {{dashboard_url}}

Met vriendelijke groet,
AnsCheckt Team

---
Om deze e-mails niet meer te ontvangen, bezoek: {{opt_out_url}}""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">📊 Your Weekly Digest</h2>
    <p>Hi <strong>{{user_name}}</strong>,</p>
    <p>Here's your weekly summary of AnsCheckt activity:</p>
    <div style="background: #f9fafb; padding: 1em; border-radius: 0.5em; margin: 1em 0;">
        <p style="margin: 0.5em 0;"><strong>Submissions This Week:</strong> {{submission_count}}</p>
        <p style="margin: 0.5em 0;"><strong>Reviews Completed:</strong> {{review_count}}</p>
        <p style="margin: 0.5em 0;"><strong>Fact-Checks Published:</strong> {{published_count}}</p>
    </div>
    {% if top_fact_checks %}
    <h3 style="color: #2563eb;">Top Fact-Checks This Week</h3>
    <div style="background: #eff6ff; padding: 1em; border-radius: 0.5em; margin: 1em 0;">
        {{top_fact_checks}}
    </div>
    {% endif %}
    <p><a href="{{dashboard_url}}" style="display: inline-block; background: #2563eb; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">View Dashboard</a></p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Unsubscribe from emails</a>
    </p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">📊 Uw Wekelijkse Samenvatting</h2>
    <p>Hallo <strong>{{user_name}}</strong>,</p>
    <p>Hier is uw wekelijkse samenvatting van AnsCheckt activiteit:</p>
    <div style="background: #f9fafb; padding: 1em; border-radius: 0.5em; margin: 1em 0;">
        <p style="margin: 0.5em 0;"><strong>Inzendingen Deze Week:</strong> {{submission_count}}</p>
        <p style="margin: 0.5em 0;"><strong>Reviews Voltooid:</strong> {{review_count}}</p>
        <p style="margin: 0.5em 0;"><strong>Fact-Checks Gepubliceerd:</strong> {{published_count}}</p>
    </div>
    {% if top_fact_checks %}
    <h3 style="color: #2563eb;">Top Fact-Checks Deze Week</h3>
    <div style="background: #eff6ff; padding: 1em; border-radius: 0.5em; margin: 1em 0;">
        {{top_fact_checks}}
    </div>
    {% endif %}
    <p><a href="{{dashboard_url}}" style="display: inline-block; background: #2563eb; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Bekijk Dashboard</a></p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Afmelden voor e-mails</a>
    </p>
</body>
</html>""",
        },
        "variables": {
            "user_name": "string",
            "submission_count": "number",
            "review_count": "number",
            "published_count": "number",
            "top_fact_checks": "string (optional)",
            "dashboard_url": "string",
            "opt_out_url": "string",
        },
    },
    {
        "template_key": "password_reset",
        "template_type": EmailTemplateType.PASSWORD_RESET,
        "name": {"en": "Password Reset", "nl": "Wachtwoord Reset"},
        "description": {
            "en": "Sent when user requests password reset",
            "nl": "Verzonden wanneer gebruiker wachtwoord reset aanvraagt",
        },
        "subject": {
            "en": "Reset Your Password - AnsCheckt",
            "nl": "Reset Uw Wachtwoord - AnsCheckt",
        },
        "body_text": {
            "en": """Hi {{user_name}},

We received a request to reset your password for AnsCheckt.

Reset your password here: {{reset_url}}

This link will expire in {{expiry_hours}} hours.

If you didn't request this, please ignore this email.

Best regards,
AnsCheckt Team""",
            "nl": """Hallo {{user_name}},

We hebben een verzoek ontvangen om uw wachtwoord voor AnsCheckt te resetten.

Reset uw wachtwoord hier: {{reset_url}}

Deze link vervalt over {{expiry_hours}} uur.

Als u dit niet heeft aangevraagd, negeer dan deze e-mail.

Met vriendelijke groet,
AnsCheckt Team""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #dc2626;">🔒 Password Reset Request</h2>
    <p>Hi <strong>{{user_name}}</strong>,</p>
    <p>We received a request to reset your password for AnsCheckt.</p>
    <p><a href="{{reset_url}}" style="display: inline-block; background: #dc2626; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Reset Password</a></p>
    <p style="color: #6b7280; font-size: 0.875em;">This link will expire in <strong>{{expiry_hours}} hours</strong>.</p>
    <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 1em; margin: 1em 0;">
        <p style="margin: 0;"><strong>Security Notice:</strong> If you didn't request this, please ignore this email and your password will remain unchanged.</p>
    </div>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #dc2626;">🔒 Wachtwoord Reset Verzoek</h2>
    <p>Hallo <strong>{{user_name}}</strong>,</p>
    <p>We hebben een verzoek ontvangen om uw wachtwoord voor AnsCheckt te resetten.</p>
    <p><a href="{{reset_url}}" style="display: inline-block; background: #dc2626; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Reset Wachtwoord</a></p>
    <p style="color: #6b7280; font-size: 0.875em;">Deze link vervalt over <strong>{{expiry_hours}} uur</strong>.</p>
    <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 1em; margin: 1em 0;">
        <p style="margin: 0;"><strong>Beveiligings Notificatie:</strong> Als u dit niet heeft aangevraagd, negeer dan deze e-mail en uw wachtwoord blijft ongewijzigd.</p>
    </div>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
        },
        "variables": {
            "user_name": "string",
            "reset_url": "string",
            "expiry_hours": "number",
        },
    },
    {
        "template_key": "welcome_email",
        "template_type": EmailTemplateType.WELCOME_EMAIL,
        "name": {"en": "Welcome Email", "nl": "Welkom E-mail"},
        "description": {
            "en": "Sent when new user registers",
            "nl": "Verzonden wanneer nieuwe gebruiker registreert",
        },
        "subject": {
            "en": "Welcome to AnsCheckt!",
            "nl": "Welkom bij AnsCheckt!",
        },
        "body_text": {
            "en": """Hi {{user_name}},

Welcome to AnsCheckt! We're excited to have you join our fact-checking community.

Here's how to get started:
1. Submit your first claim for fact-checking
2. Browse existing fact-checks
3. Share fact-checks with your network

Get started here: {{dashboard_url}}

If you have any questions, feel free to reach out to our team.

Best regards,
AnsCheckt Team

---
To stop receiving these emails, visit: {{opt_out_url}}""",
            "nl": """Hallo {{user_name}},

Welkom bij AnsCheckt! We zijn blij dat u deel uitmaakt van onze fact-checking community.

Zo kunt u beginnen:
1. Dien uw eerste claim in voor fact-checking
2. Bekijk bestaande fact-checks
3. Deel fact-checks met uw netwerk

Begin hier: {{dashboard_url}}

Als u vragen heeft, neem gerust contact op met ons team.

Met vriendelijke groet,
AnsCheckt Team

---
Om deze e-mails niet meer te ontvangen, bezoek: {{opt_out_url}}""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">🎉 Welcome to AnsCheckt!</h2>
    <p>Hi <strong>{{user_name}}</strong>,</p>
    <p>Welcome to AnsCheckt! We're excited to have you join our fact-checking community.</p>
    <h3 style="color: #2563eb;">Get Started:</h3>
    <ol style="line-height: 2;">
        <li>Submit your first claim for fact-checking</li>
        <li>Browse existing fact-checks</li>
        <li>Share fact-checks with your network</li>
    </ol>
    <p><a href="{{dashboard_url}}" style="display: inline-block; background: #2563eb; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Go to Dashboard</a></p>
    <p>If you have any questions, feel free to reach out to our team.</p>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Unsubscribe from emails</a>
    </p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">🎉 Welkom bij AnsCheckt!</h2>
    <p>Hallo <strong>{{user_name}}</strong>,</p>
    <p>Welkom bij AnsCheckt! We zijn blij dat u deel uitmaakt van onze fact-checking community.</p>
    <h3 style="color: #2563eb;">Begin:</h3>
    <ol style="line-height: 2;">
        <li>Dien uw eerste claim in voor fact-checking</li>
        <li>Bekijk bestaande fact-checks</li>
        <li>Deel fact-checks met uw netwerk</li>
    </ol>
    <p><a href="{{dashboard_url}}" style="display: inline-block; background: #2563eb; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Ga naar Dashboard</a></p>
    <p>Als u vragen heeft, neem gerust contact op met ons team.</p>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 2em 0;">
    <p style="font-size: 0.875em; color: #6b7280;">
        <a href="{{opt_out_url}}" style="color: #2563eb;">Afmelden voor e-mails</a>
    </p>
</body>
</html>""",
        },
        "variables": {
            "user_name": "string",
            "dashboard_url": "string",
            "opt_out_url": "string",
        },
    },
    {
        "template_key": "account_verification",
        "template_type": EmailTemplateType.ACCOUNT_VERIFICATION,
        "name": {"en": "Account Verification", "nl": "Account Verificatie"},
        "description": {
            "en": "Sent to verify new user email address",
            "nl": "Verzonden om nieuw gebruikers e-mailadres te verifiëren",
        },
        "subject": {
            "en": "Verify Your Email - AnsCheckt",
            "nl": "Verifieer Uw E-mail - AnsCheckt",
        },
        "body_text": {
            "en": """Hi {{user_name}},

Thank you for registering with AnsCheckt!

Please verify your email address by clicking the link below:
{{verification_url}}

This link will expire in {{expiry_hours}} hours.

If you didn't create an account, please ignore this email.

Best regards,
AnsCheckt Team""",
            "nl": """Hallo {{user_name}},

Bedankt voor het registreren bij AnsCheckt!

Verifieer uw e-mailadres door op de onderstaande link te klikken:
{{verification_url}}

Deze link vervalt over {{expiry_hours}} uur.

Als u geen account heeft aangemaakt, negeer dan deze e-mail.

Met vriendelijke groet,
AnsCheckt Team""",
        },
        "body_html": {
            "en": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">✉️ Verify Your Email</h2>
    <p>Hi <strong>{{user_name}}</strong>,</p>
    <p>Thank you for registering with AnsCheckt!</p>
    <p>Please verify your email address to activate your account:</p>
    <p><a href="{{verification_url}}" style="display: inline-block; background: #2563eb; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Verify Email Address</a></p>
    <p style="color: #6b7280; font-size: 0.875em;">This link will expire in <strong>{{expiry_hours}} hours</strong>.</p>
    <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 1em; margin: 1em 0;">
        <p style="margin: 0;">If you didn't create an account, please ignore this email.</p>
    </div>
    <p>Best regards,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
            "nl": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">✉️ Verifieer Uw E-mail</h2>
    <p>Hallo <strong>{{user_name}}</strong>,</p>
    <p>Bedankt voor het registreren bij AnsCheckt!</p>
    <p>Verifieer uw e-mailadres om uw account te activeren:</p>
    <p><a href="{{verification_url}}" style="display: inline-block; background: #2563eb; color: white; padding: 0.75em 1.5em; text-decoration: none; border-radius: 0.5em;">Verifieer E-mailadres</a></p>
    <p style="color: #6b7280; font-size: 0.875em;">Deze link vervalt over <strong>{{expiry_hours}} uur</strong>.</p>
    <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 1em; margin: 1em 0;">
        <p style="margin: 0;">Als u geen account heeft aangemaakt, negeer dan deze e-mail.</p>
    </div>
    <p>Met vriendelijke groet,<br><strong>AnsCheckt Team</strong></p>
</body>
</html>""",
        },
        "variables": {
            "user_name": "string",
            "verification_url": "string",
            "expiry_hours": "number",
        },
    },
]


async def seed_templates() -> None:
    """Seed email templates into the database"""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        service = EmailTemplateService()

        for template_data in TEMPLATES:
            try:
                # Check if template already exists
                existing = await service.get_template(
                    session, template_data["template_key"], include_inactive=True
                )

                if existing:
                    print(f"✓ Template '{template_data['template_key']}' already exists, skipping")
                    continue

                # Create template
                await service.create_template(session, **template_data)
                print(f"✓ Created template: {template_data['template_key']}")

            except Exception as e:
                print(f"✗ Error creating template '{template_data['template_key']}': {e}")

    await engine.dispose()
    print("\n✅ Template seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_templates())
