# Generated migration for chatbot models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('properties', '0002_nearbylocation_latitude_nearbylocation_longitude_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatbotConversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visitor_name', models.CharField(blank=True, max_length=255, null=True)),
                ('visitor_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('visitor_phone', models.CharField(blank=True, max_length=20, null=True)),
                ('visitor_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('property', models.ForeignKey(blank=True, help_text='Property being inquired about (null for general inquiry)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chatbot_conversations', to='properties.property')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chatbot_conversations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ChatbotMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender', models.CharField(choices=[('user', 'User'), ('bot', 'AI Bot')], default='user', max_length=10)),
                ('message', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('ai_confidence', models.FloatField(blank=True, null=True)),
                ('intent_detected', models.CharField(blank=True, choices=[('inquiry', 'General Inquiry'), ('pricing', 'Pricing Question'), ('schedule', 'Schedule Tour'), ('lead_qualify', 'Lead Qualification'), ('document', 'Document Request'), ('other', 'Other')], max_length=50, null=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chatbot.chatbotconversation')),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
        migrations.CreateModel(
            name='Lead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=20)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('property_type_preference', models.CharField(blank=True, choices=[('apartment', 'Apartment'), ('villa', 'Villa'), ('house', 'Independent House'), ('plot', 'Plot/Land'), ('commercial', 'Commercial Space')], max_length=50, null=True)),
                ('budget_min', models.DecimalField(blank=True, decimal_places=2, help_text='Minimum budget', max_digits=12, null=True)),
                ('budget_max', models.DecimalField(blank=True, decimal_places=2, help_text='Maximum budget', max_digits=12, null=True)),
                ('buyer_type', models.CharField(blank=True, choices=[('buyer', 'Buyer'), ('renter', 'Renter'), ('agent', 'Agent'), ('investor', 'Investor')], max_length=20, null=True)),
                ('timeline', models.CharField(blank=True, choices=[('immediate', 'Immediate (0-2 weeks)'), ('soon', 'Soon (1-3 months)'), ('later', 'Later (3-6 months)'), ('flexible', 'Flexible/Exploring')], help_text='Timeline for purchase/rent', max_length=50, null=True)),
                ('status', models.CharField(choices=[('new', 'New'), ('contacted', 'Contacted'), ('qualified', 'Qualified'), ('scheduled', 'Appointment Scheduled'), ('closed', 'Closed'), ('lost', 'Lost')], default='new', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('notes', models.TextField(blank=True, help_text='Internal notes from bot/agent')),
                ('assigned_agent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_leads', to=settings.AUTH_USER_MODEL)),
                ('conversation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='lead', to='chatbot.chatbotconversation')),
                ('interested_property', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='interested_leads', to='properties.property')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_type', models.CharField(choices=[('property_tour', 'Property Tour'), ('consultation', 'Virtual Consultation'), ('document_review', 'Document Review'), ('follow_up', 'Follow-up Call')], default='property_tour', max_length=50)),
                ('scheduled_at', models.DateTimeField(help_text='Desired appointment datetime')),
                ('status', models.CharField(choices=[('pending', 'Pending Confirmation'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('rescheduled', 'Rescheduled')], default='pending', max_length=20)),
                ('agent_confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('confirmation_sent', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True, help_text='Tour notes or special requests')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_agent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='scheduled_appointments', to=settings.AUTH_USER_MODEL)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='chatbot.lead')),
                ('property', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='scheduled_tours', to='properties.property')),
            ],
            options={
                'ordering': ['scheduled_at'],
            },
        ),
        migrations.CreateModel(
            name='ChatbotAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('total_conversations', models.IntegerField(default=0)),
                ('total_messages', models.IntegerField(default=0)),
                ('leads_qualified', models.IntegerField(default=0)),
                ('appointments_scheduled', models.IntegerField(default=0)),
                ('avg_conversation_duration', models.IntegerField(default=0, help_text='In seconds')),
                ('avg_messages_per_conversation', models.FloatField(default=0)),
            ],
            options={
                'verbose_name_plural': 'Chatbot Analytics',
                'ordering': ['-date'],
            },
        ),
    ]
