from django.db import models
from django.conf import settings
from properties.models import Property


class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender.email} regarding {self.property.title}"


class ChatThread(models.Model):
    """One thread per buyer per listing (WebSocket chat)."""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='chat_threads')
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='buyer_chat_threads',
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agent_chat_threads',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['property', 'buyer'], name='uniq_chat_thread_property_buyer'),
        ]

    def __str__(self):
        return f"Chat: {self.property.title} / {self.buyer.email}"


class ChatMessage(models.Model):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sent')
    body = models.TextField()
    is_ai_bot = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.body[:40]
