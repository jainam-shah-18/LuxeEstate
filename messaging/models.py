from django.db import models
from django.contrib.auth.models import User
from properties.models import Property
from django.utils import timezone


class Conversation(models.Model):
    """Represents a conversation between two users about a property"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='conversations')
    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_conversations')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_conversations')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ('property', 'initiator', 'recipient')
    
    def __str__(self):
        return f"Conversation between {self.initiator.username} and {self.recipient.username} about {self.property.title}"


class Message(models.Model):
    """Individual messages in a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True)
    
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    
    # Message attachments
    image = models.ImageField(upload_to='message_attachments/%Y/%m/%d/', blank=True, null=True)
    
    # Message type (for future use - document sharing, etc)
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text'),
            ('image', 'Image'),
            ('document', 'Document'),
        ],
        default='text'
    )

    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"

    def save(self, *args, **kwargs):
        if self.conversation_id and not self.property_id:
            self.property_id = self.conversation.property_id
        super().save(*args, **kwargs)
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class ChatNotification(models.Model):
    """Notifications for new messages"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_notifications')
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username}"


class AgentResponse(models.Model):
    """Quick responses for agents - canned messages"""
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quick_responses')
    title = models.CharField(max_length=100)
    message_template = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.agent.username} - {self.title}"
