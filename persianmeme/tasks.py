from .models import Voice
from background_task import background
from .functions import delete_vote_sync
from zoneinfo import ZoneInfo
from datetime import datetime
from background_task.models import CompletedTask


@background(schedule=21600)
def revoke_review(voice_id: int):
    try:
        target_voice = Voice.objects.get(id=voice_id, reviewed=False)
    except Voice.DoesNotExist:
        return
    target_voice.assigned_admin = None
    target_voice.save()


@background(schedule=21600)
def check_voice(voice_id: int):
    CompletedTask.objects.all().delete()
    if datetime.now(ZoneInfo('Asia/Tehran')).hour < 8:
        return check_voice(voice_id)
    try:
        voice = Voice.objects.get(id=voice_id, status='p')
    except Voice.DoesNotExist:
        return
    accept_count = voice.accept_vote.count()
    deny_count = voice.deny_vote.count()
    if accept_count == deny_count == 0:
        return check_voice(voice_id)
    else:
        delete_vote_sync(voice.message_id)
        if accept_count >= deny_count:
            voice.accept()
        else:
            voice.deny()


@background(schedule=180)
def update_votes(voice_id: int):
    try:
        voice = Voice.objects.get(id=voice_id, status=Voice.Status.PENDING)
    except Voice.DoesNotExist:
        return
    voice.edit_vote_count()
    update_votes(voice_id)
