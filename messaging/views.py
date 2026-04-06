from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from properties.models import Property

from .models import ChatMessage, ChatThread, Message


@login_required
@require_POST
def contact_agent(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    body = (request.POST.get('message') or '').strip()
    if not body:
        messages.error(request, 'Please enter a message.')
        return redirect('properties:property_detail', pk=pk)

    if prop.agent_id == request.user.id:
        messages.warning(request, 'You are the listing owner.')
        return redirect('properties:property_detail', pk=pk)

    Message.objects.create(sender=request.user, property=prop, message=body)
    messages.success(request, 'Your message was sent to the agent.')
    return redirect('properties:property_detail', pk=pk)


@login_required
def inbox(request):
    received = Message.objects.filter(property__agent=request.user).select_related(
        'sender', 'property'
    ).order_by('-created_at')
    sent = Message.objects.filter(sender=request.user).select_related('property').order_by('-created_at')
    return render(request, 'messaging/inbox.html', {'received': received, 'sent': sent})


@login_required
def chat_threads(request):
    threads = (
        ChatThread.objects.filter(Q(buyer=request.user) | Q(agent=request.user))
        .select_related('property', 'buyer', 'agent')
        .order_by('-updated_at')
    )
    return render(request, 'messaging/chat_threads.html', {'threads': threads})


@login_required
def chat_room(request, thread_id):
    thread = get_object_or_404(
        ChatThread.objects.select_related('property', 'buyer', 'agent'),
        pk=thread_id,
    )
    if request.user.id not in (thread.buyer_id, thread.agent_id):
        return HttpResponseForbidden('You cannot access this chat.')

    msgs = thread.chat_messages.select_related('sender').order_by('created_at')
    return render(
        request,
        'messaging/chat_room.html',
        {
            'thread': thread,
            'chat_messages': msgs,
        },
    )


@login_required
def start_chat(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    if prop.agent_id == request.user.id:
        messages.info(request, 'You cannot chat with yourself.')
        return redirect('properties:property_detail', pk=pk)

    thread, _ = ChatThread.objects.get_or_create(
        property=prop,
        buyer=request.user,
        defaults={'agent': prop.agent},
    )
    return redirect('messaging:chat_room', thread_id=thread.pk)
