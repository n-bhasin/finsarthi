# Generated by Django 2.2.5 on 2019-11-26 18:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='information',
            name='user_assign',
        ),
        migrations.AddField(
            model_name='contact',
            name='status',
            field=models.BooleanField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contact_handler', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='information',
            name='appointment_follow_up',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='information',
            name='callback_follow_up',
            field=models.CharField(max_length=100, null=True),
        ),
    ]