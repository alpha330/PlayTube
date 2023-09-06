# Generated by Django 4.1.2 on 2023-08-29 17:51

from django.db import migrations, models
import play.uploadpathsetters
import play.validators


class Migration(migrations.Migration):

    dependencies = [
        ('play', '0024_alter_history_options_remove_video_preview_images_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='channel',
            name='profile_picture',
        ),
        migrations.AddField(
            model_name='channel',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to=play.uploadpathsetters.getChannelAvatarUploadPath, validators=[play.validators.validate_upload_image_file]),
        ),
        migrations.AddField(
            model_name='channel',
            name='banner',
            field=models.ImageField(blank=True, null=True, upload_to=play.uploadpathsetters.getChannelBannerUploadPath, validators=[play.validators.validate_upload_image_file]),
        ),
    ]