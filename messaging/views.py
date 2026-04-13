from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from properties.models import Property
from .models import Message, Conversation, ChatNotification
import json


# ============================================
# Conversation Views
# ============================================

@login_required
def conversation_list(request):
    """List all conversations for the logged-in user"""
    conversations = Conversation.objects.filter(
        Q(initiator=request.user) | Q(recipient=request.user)
    ).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    ).order_by('-updated_at')
    
    # Pagination
    paginator = Paginator(conversations, 20)
    page = request.GET.get('page')
    
    try:
        conversations_page = paginator.page(page)
    except PageNotAnInteger:
        conversations_page = paginator.page(1)
    except EmptyPage:
        conversations_page = paginator.page(paginator.num_pages)
    
    context = {
        'conversations': conversations_page,
        'paginator': paginator,
        'unread_count': sum(1 for c in conversations if c.unread_count > 0)
    }
    return render(request, 'messaging/conversation_list.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """View conversation details and messages"""
    conversation = get_object_or_404(
        Conversation,
        pk=conversation_id
    )
    
    # Check permissions
    if request.user not in [conversation.initiator, conversation.recipient]:
        django_messages.error(request, 'Permission denied.')
        return redirect('messaging:conversation_list')
    
    # Get messages
    messages = conversation.messages.all().order_by('created_at')
    
    # Mark messages as read
    messages.filter(recipient=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    # Handle AJAX GET for polling new messages
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'messages': [
                {
                    'id': msg.id,
                    'sender': msg.sender.get_full_name() or msg.sender.username,
                    'sender_id': msg.sender.id,
                    'message': msg.message,
                    'created_at': msg.created_at.isoformat(),
                    'message_type': msg.message_type,
                    'is_read': msg.is_read,
                }
                for msg in messages
            ]
        })
    
    # Handle new message
    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        
        if message_text:
            # Determine recipient
            recipient = conversation.recipient if request.user == conversation.initiator else conversation.initiator
            
            # Create message
            msg = Message.objects.create(
                conversation=conversation,
                property=conversation.property,
                sender=request.user,
                recipient=recipient,
                message=message_text
            )
            
            # Handle image if provided
            if 'image' in request.FILES:
                msg.image = request.FILES['image']
                msg.message_type = 'image'
                msg.save()
            
            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save()
            
            # Create notification for recipient
            ChatNotification.objects.create(
                user=recipient,
                message=msg
            )
            
            # Return JSON for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': msg.id,
                        'sender': msg.sender.get_full_name() or msg.sender.username,
                        'message': msg.message,
                        'created_at': msg.created_at.strftime('%H:%M'),
                        'message_type': msg.message_type
                    }
                })
        
        return redirect('messaging:conversation_detail', conversation_id=conversation_id)
    
    # Pagination for messages
    paginator = Paginator(messages, 20)
    page = request.GET.get('page', 1)
    
    try:
        messages_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        messages_page = paginator.page(1)
    
    context = {
        'conversation': conversation,
        'messages': messages_page,
        'paginator': paginator,
    }
    return render(request, 'messaging/conversation_detail.html', context)


# ============================================
# Contact Agent View (from Property)
# ============================================

@login_required
def contact_agent(request, property_id):
    """Initiate contact with agent about a property"""
    property = get_object_or_404(Property, pk=property_id)
    agent = property.agent
    
    if request.user == agent:
        django_messages.error(request, 'You cannot message your own property.')
        return redirect('properties:detail', pk=property_id)
    
    # Get or create conversation
    conversation, created = Conversation.objects.get_or_create(
        property=property,
        initiator=request.user,
        recipient=agent,
    )

    initial_message = request.POST.get('message', '').strip()
    if request.method == 'POST' and initial_message:
        msg = Message.objects.create(
            conversation=conversation,
            property=property,
            sender=request.user,
            recipient=agent,
            message=initial_message
        )
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])
        ChatNotification.objects.create(user=agent, message=msg)
    
    return redirect('messaging:conversation_detail', conversation_id=conversation.id)


@login_required
def send_message(request, property_id):
    """Send message to agent (alternate endpoint)"""
    property = get_object_or_404(Property, pk=property_id)
    
    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        
        if not message_text:
            return JsonResponse({'success': False, 'error': 'Message cannot be empty'})
        
        # Get or create conversation
        conversation, created = Conversation.objects.get_or_create(
            property=property,
            initiator=request.user,
            recipient=property.agent,
        )
        
        # Create message
        msg = Message.objects.create(
            conversation=conversation,
            property=property,
            sender=request.user,
            recipient=property.agent,
            message=message_text
        )
        
        # Handle image if provided
        if 'image' in request.FILES:
            msg.image = request.FILES['image']
            msg.message_type = 'image'
            msg.save()
        
        # Update conversation
        conversation.updated_at = timezone.now()
        conversation.save()
        
        # Create notification
        ChatNotification.objects.create(
            user=property.agent,
            message=msg
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        django_messages.success(request, 'Message sent successfully!')
        return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    
    return JsonResponse({'error': 'Invalid method'}, status=400)


# ============================================
# Notification Views
# ============================================

@login_required
def get_notifications(request):
    """Get unread notifications (AJAX)"""
    notifications = ChatNotification.objects.filter(
        user=request.user,
        is_read=False
    ).select_related('message__sender', 'message__conversation').order_by('-created_at')[:10]
    
    data = {
        'unread_count': notifications.count(),
        'notifications': []
    }
    
    for notif in notifications:
        data['notifications'].append({
            'id': notif.id,
            'sender': notif.message.sender.get_full_name() or notif.message.sender.username,
            'message_preview': notif.message.message[:50] + ('...' if len(notif.message.message) > 50 else ''),
            'conversation_id': notif.message.conversation.id,
            'created_at': notif.created_at.strftime('%H:%M'),
        })
    
    return JsonResponse(data)


@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(ChatNotification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('messaging:conversation_detail', conversation_id=notification.message.conversation.id)


# ============================================
# Backward Compatibility Views
# ============================================

@login_required
def contact_list(request):
    """Legacy contact list - redirects to conversation list"""
    return redirect('messaging:conversation_list')


@login_required
def chat(request, property_id):
    """Legacy chat view - redirects to proper conversation"""
    property = get_object_or_404(Property, pk=property_id)
    
    conversation, created = Conversation.objects.get_or_create(
        property=property,
        initiator=request.user,
        recipient=property.agent,
    )
    
    return redirect('messaging:conversation_detail', conversation_id=conversation.id)
