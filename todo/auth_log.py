import logging
from django.utils import timezone

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.http import HttpRequest

logger = logging.getLogger('auth_log')


# Обработчик сигнала входа пользователя. Логирует информацию о входе
@receiver(user_logged_in)
def log_login(sender, request: HttpRequest, user, **kwargs):
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
    time = timezone.now()

    log_message = (
        f'\n'
        f"Пользователь - {user.id} ({user.username}) вошел в систему.\n"
        f"IP-адрес: {ip_address}\n"
        f"User-Agent: {user_agent}\n"
        f"Время: {time}\n"
    )

    logger.info(log_message)
