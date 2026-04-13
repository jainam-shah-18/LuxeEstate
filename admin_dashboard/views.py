from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from properties.models import Property, PropertyImage
from accounts.models import Profile, UserPropertyView
from messaging.models import Conversation, Message
from payments.models import Payment, PaymentPackage
from favorites.models import Favorite
from django.contrib.auth.models import User


def is_admin(user):
    """Check if user is admin"""
    return user.is_superuser or (hasattr(user, 'profile') and user.profile.role == 'admin')


@login_required
def admin_dashboard(request):
    """Main admin dashboard"""
    if not is_admin(request.user):
        # Redirect to regular dashboard if user is agent
        if request.user.profile.role == 'agent':
            return render(request, 'accounts/agent_dashboard.html', {
                'properties': request.user.properties.all()
            })
        return render(request, 'accounts/buyer_dashboard.html')
    
    # System-wide statistics
    stats = {
        'total_users': User.objects.count(),
        'total_agents': Profile.objects.filter(role='agent').count(),
        'total_buyers': Profile.objects.filter(role='buyer').count(),
        'total_properties': Property.objects.count(),
        'active_properties': Property.objects.filter(is_active=True).count(),
        'total_conversations': Conversation.objects.count(),
        'total_messages': Message.objects.count(),
        'total_revenue': Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    
    # Recent activity
    recent_properties = Property.objects.all().order_by('-created_at')[:5]
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    recent_payments = Payment.objects.filter(status='completed').order_by('-completed_at')[:10]
    
    # Chart data
    days_back = 30
    date_stats = []
    
    for i in range(days_back, -1, -1):
        date = timezone.now() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        properties_created = Property.objects.filter(
            created_at__date=date
        ).count()
        
        users_joined = User.objects.filter(
            date_joined__date=date
        ).count()
        
        revenue = Payment.objects.filter(
            status='completed',
            completed_at__date=date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        date_stats.append({
            'date': date_str,
            'properties': properties_created,
            'users': users_joined,
            'revenue': float(revenue),
        })
    
    context = {
        'stats': stats,
        'recent_properties': recent_properties,
        'recent_users': recent_users,
        'recent_payments': recent_payments,
        'date_stats': date_stats,
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)


@login_required
def user_analytics(request):
    """User analytics"""
    if not is_admin(request.user):
        return render(request, 'admin_dashboard/unauthorized.html')
    
    # User statistics
    total_users = User.objects.count()
    verified_users = Profile.objects.filter(email_verified=True).count()
    unverified_users = total_users - verified_users
    
    # Users by role
    users_by_role = Profile.objects.values('role').annotate(count=Count('role'))
    
    # Top active users (by property views)
    top_users = User.objects.annotate(
        views_count=Count('property_views')
    ).order_by('-views_count')[:10]
    
    # New users in last 30 days
    new_users_30days = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    context = {
        'total_users': total_users,
        'verified_users': verified_users,
        'unverified_users': unverified_users,
        'users_by_role': users_by_role,
        'top_users': top_users,
        'new_users_30days': new_users_30days,
    }
    
    return render(request, 'admin_dashboard/user_analytics.html', context)


@login_required
def property_analytics(request):
    """Property analytics"""
    if not is_admin(request.user):
        return render(request, 'admin_dashboard/unauthorized.html')
    
    # Property statistics
    total_properties = Property.objects.count()
    active_properties = Property.objects.filter(is_active=True).count()
    inactive_properties = total_properties - active_properties
    
    # Properties by type
    properties_by_type = Property.objects.values('property_type').annotate(
        count=Count('property_type')
    ).order_by('-count')
    
    # Properties by city
    properties_by_city = Property.objects.values('city').annotate(
        count=Count('city')
    ).order_by('-count')[:10]
    
    # Top viewed properties
    top_properties = Property.objects.annotate(
        views_count=Count('viewed_by')
    ).order_by('-views_count')[:10]
    
    # Average property price
    avg_price = Property.objects.aggregate(Avg('price'))['price__avg'] or 0
    
    # New properties in last 30 days
    new_properties_30days = Property.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    # Featured properties
    featured_properties = Property.objects.filter(is_featured=True).count()
    promoted_properties = Property.objects.filter(is_promoted=True).count()
    
    context = {
        'total_properties': total_properties,
        'active_properties': active_properties,
        'inactive_properties': inactive_properties,
        'properties_by_type': properties_by_type,
        'properties_by_city': properties_by_city,
        'top_properties': top_properties,
        'avg_price': f"₹{avg_price:,.0f}",
        'new_properties_30days': new_properties_30days,
        'featured_properties': featured_properties,
        'promoted_properties': promoted_properties,
    }
    
    return render(request, 'admin_dashboard/property_analytics.html', context)


@login_required
def revenue_analytics(request):
    """Revenue and payment analytics"""
    if not is_admin(request.user):
        return render(request, 'admin_dashboard/unauthorized.html')
    
    # Payment statistics
    total_revenue = Payment.objects.filter(
        status='completed'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    completed_payments = Payment.objects.filter(status='completed').count()
    failed_payments = Payment.objects.filter(status='failed').count()
    pending_payments = Payment.objects.filter(status='pending').count()
    
    # Revenue by package
    revenue_by_package = Payment.objects.filter(
        status='completed'
    ).values('package__name').annotate(
        revenuet=Sum('amount'),
        count=Count('id')
    )
    
    # Monthly revenue
    monthly_revenue = []
    for i in range(11, -1, -1):
        month_start = timezone.now().replace(day=1) - timedelta(days=i*30)
        month_end = month_start + timedelta(days=30)
        
        revenue = Payment.objects.filter(
            status='completed',
            completed_at__range=[month_start, month_end]
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        monthly_revenue.append({
            'month': month_start.strftime('%B'),
            'revenue': float(revenue),
        })
    
    context = {
        'total_revenue': f"₹{total_revenue:,.0f}",
        'completed_payments': completed_payments,
        'failed_payments': failed_payments,
        'pending_payments': pending_payments,
        'revenue_by_package': revenue_by_package,
        'monthly_revenue': monthly_revenue,
    }
    
    return render(request, 'admin_dashboard/revenue_analytics.html', context)


@login_required
def engagement_analytics(request):
    """User engagement analytics"""
    if not is_admin(request.user):
        return render(request, 'admin_dashboard/unauthorized.html')
    
    # Messaging statistics
    total_conversations = Conversation.objects.count()
    total_messages = Message.objects.count()
    avg_messages_per_conversation = total_messages / total_conversations if total_conversations > 0 else 0
    
    # Favorite statistics
    total_favorites = Favorite.objects.count()
    most_favorited_properties = Property.objects.annotate(
        favorite_count=Count('favorite_set')
    ).order_by('-favorite_count')[:10]
    
    # Property view statistics
    total_views = UserPropertyView.objects.count()
    avg_views_per_property = Property.objects.aggregate(
        avg_views=Avg('views_count')
    )['avg_views'] or 0
    
    context = {
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'avg_messages_per_conversation': f"{avg_messages_per_conversation:.0f}",
        'total_favorites': total_favorites,
        'most_favorited_properties': most_favorited_properties,
        'total_views': total_views,
        'avg_views_per_property': f"{avg_views_per_property:.0f}",
    }
    
    return render(request, 'admin_dashboard/engagement_analytics.html', context)
