"""Business actions shared by the owner portal, dashboard and seed command."""
from django.urls import reverse

from accounts.models import Notification

from .constants import OWNER_STATUS_HELP, Status
from .models import StatusHistory


def log_activity(submission, user, action, details=""):
    from acquisitions.models import ActivityLog

    return ActivityLog.objects.create(
        submission=submission, user=user if user and user.is_authenticated else None, action=action, details=details
    )


def notify_owner(submission, title, message=""):
    if submission.owner_user_id:
        Notification.objects.create(
            user=submission.owner_user,
            title=title,
            message=message,
            url=reverse("submissions:owner_submission", args=[submission.reference_id]),
        )


def change_status(submission, new_status, user=None, note=""):
    """Move a submission to a new pipeline status, keeping history, log and notification."""
    if new_status not in Status.values:
        raise ValueError(f"Invalid status {new_status}")
    old_status = submission.status
    if old_status == new_status:
        return False
    submission.status = new_status
    submission.save(update_fields=["status", "updated_at"])
    StatusHistory.objects.create(
        submission=submission,
        old_status=old_status,
        new_status=new_status,
        note=note,
        changed_by=user if user and user.is_authenticated else None,
    )
    label = Status(new_status).label
    log_activity(submission, user, f"Status changed to {label}", note)
    notify_owner(submission, f"{submission.reference_id}: {label}", note or OWNER_STATUS_HELP.get(new_status, ""))
    return True
