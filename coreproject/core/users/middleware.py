from datetime import datetime
from django.utils.deprecation import MiddlewareMixin
from .models import UserActivity
from .tasks import send_activity_status_task


class UserActivityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            UserActivity.objects.update_or_create(
                user=request.user,
                defaults={
                    'last_activity': datetime.now(),
                    'is_active': True
                }
            )

            send_activity_status_task.delay(request.user.id)
