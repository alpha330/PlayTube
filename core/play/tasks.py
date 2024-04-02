from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.conf import settings
import subprocess
import os


@shared_task
def handle_video_post_upload(video_path, video_id, subtitle_path, uploader_email, uploader_name):
    '''
    This function will be called when a video is uploaded
    '''
    transcoding = transcode.apply_async(
        args=[video_path, video_id, subtitle_path, uploader_email, uploader_name],
        retry=True,
        retry_policy={
            'max_retries': 3,  # max retries before giving up
            'interval_start': 0,  # first retry immediately
            'interval_step': 0.2,  # wait 0.2s between retries
            'interval_max': 0.2,  # but no longer than 0.2s
        }
    )


@shared_task
def transcode(video_path, video_id, subtitle_path, uploader_email, uploader_name):
    # output_path
    video_dir = os.path.dirname(video_path)
    video_title = os.path.basename(video_path).split(".")[0].replace('_', ' ')

    # get doamin name of the server
    domain_name = settings.DOMAIN_NAME
    # get http protocol to be used
    http_protocol = 'https' if settings.USE_HTTPS else 'http'

    api_endpoint = f'{http_protocol}://{domain_name}/api/get-video-stream/{video_id}'
    subprocess.run(['./create-hls-vod.sh', video_dir,
                   video_path, api_endpoint, subtitle_path])

    os.makedirs(f'{video_dir}/preview_images', exist_ok=True)

    subprocess.run([
        'ffmpeg', '-i', video_path, '-vf', 'fps=1/10,scale=120:-1', f'{video_dir}/preview_images/preview%d.jpg', '-hide_banner', '-loglevel', 'warning', '-y'
    ])

    # notify user

    body = f'Your recent video titled "{video_title}" has been processed and is available to be watched at the below link.'
    html_message = render_to_string('play/email/video_processed.html', {
        'uploader_name': uploader_name,
        'video_title': video_title,
        'message': body,
        'video_url': f'{http_protocol}://{domain_name}/watch/?v={video_id}',
        'domain_name': domain_name,
    })
    plain_message = strip_tags(html_message)
    subject = f'Hey {uploader_name}, your video has been processed. Watch it now!'

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[uploader_email],
        fail_silently=False,
        html_message=html_message
    )
