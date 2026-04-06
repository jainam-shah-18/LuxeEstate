from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView


class ChatbotDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Agent dashboard for chatbot leads and appointments."""
    
    template_name = 'chatbot/dashboard.html'
    
    def test_func(self):
        """Only agents/staff can access."""
        return self.request.user.is_staff or hasattr(self.request.user, 'agent_profile')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
