# Generated migration for TelegramUser model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0006_lead_appointment_lead_properties__status_a1fe11_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TelegramUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_id', models.BigIntegerField(db_index=True, help_text='Telegram user ID', unique=True)),
                ('telegram_username', models.CharField(blank=True, help_text='Telegram @username', max_length=255, null=True)),
                ('telegram_first_name', models.CharField(blank=True, max_length=255, null=True)),
                ('telegram_last_name', models.CharField(blank=True, max_length=255, null=True)),
                ('session_id', models.CharField(db_index=True, help_text='LuxeAI session ID for this Telegram user', max_length=255, unique=True)),
                ('conversation_state', models.JSONField(blank=True, default=dict, help_text='Current conversation state with chatbot')),
                ('message_count', models.PositiveIntegerField(default=0, help_text='Number of messages exchanged')),
                ('last_message_text', models.TextField(blank=True, null=True)),
                ('last_message_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('is_connected', models.BooleanField(db_index=True, default=True, help_text='User is actively using Telegram bot')),
                ('connection_started_at', models.DateTimeField(auto_now_add=True)),
                ('last_active_at', models.DateTimeField(auto_now=True)),
                ('language', models.CharField(choices=[('en', 'English'), ('hi', 'Hindi')], default='en', max_length=10)),
                ('receive_notifications', models.BooleanField(default=True)),
                ('lead', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='telegram_users', to='properties.lead')),
            ],
            options={
                'ordering': ['-last_active_at'],
            },
        ),
        migrations.AddIndex(
            model_name='telegramuser',
            index=models.Index(fields=['telegram_id'], name='properties_t_telegr_idx'),
        ),
        migrations.AddIndex(
            model_name='telegramuser',
            index=models.Index(fields=['session_id'], name='properties_t_session_idx'),
        ),
        migrations.AddIndex(
            model_name='telegramuser',
            index=models.Index(fields=['-last_active_at'], name='properties_t_last_ac_idx'),
        ),
        migrations.AddIndex(
            model_name='telegramuser',
            index=models.Index(fields=['is_connected', '-last_active_at'], name='properties_t_is_con_idx'),
        ),
    ]
