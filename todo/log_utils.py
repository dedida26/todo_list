import logging
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, pre_delete
from .models import Folder, Page, Task

logger = logging.getLogger('general_log')  # общий логгер для всех моделей


# Функция для логирования действий с объектами моделей
def log_action(user_id, username, model_name, object_id, action_type, time):
    log_message = f"User {user_id} ({username}): {action_type} {model_name} {object_id} at {time}"
    logger.info(log_message)


# Функция для логирования чтения объектов моделей
def log_read_action(user_id, username, model_name, object_id):
    time = timezone.now().isoformat()
    log_message = f"User {user_id} ({username}): READ {model_name} {object_id} at {time}"
    logger.info(log_message)


# --- Обработчики сигналов для модели Folder ---
@receiver(pre_save, sender=Folder)
def log_folder_pre_save(sender, instance, **kwargs):
    if instance.pk:  # Проверяем, существует ли запись/обновление
        log_action(instance.owner.id, instance.owner.username, "Folder", instance.pk,
                   "UPDATED", timezone.now().isoformat())


@receiver(post_save, sender=Folder)
def log_folder_post_save(sender, instance, created, **kwargs):
    if created:  # Проверяем, создана ли новая запись
        log_action(instance.owner.id, instance.owner.username, "Folder", instance.pk,
                   "CREATED", timezone.now().isoformat())


@receiver(pre_delete, sender=Folder)
def log_folder_pre_delete(sender, instance, **kwargs):
    log_action(instance.owner.id, instance.owner.username, "Folder", instance.pk,
               "DELETED", timezone.now().isoformat())


# Обработчики сигналов для модели Page
@receiver(pre_save, sender=Page)
def log_page_pre_save(sender, instance, **kwargs):
    if instance.pk:
        log_action(instance.created_by.id, instance.created_by.username, "Page", instance.pk,
                   "UPDATED", timezone.now().isoformat())


@receiver(post_save, sender=Page)
def log_page_post_save(sender, instance, created, **kwargs):
    if created:
        log_action(instance.created_by.id, instance.created_by.username, "Page", instance.pk,
                   "CREATED", timezone.now().isoformat())


@receiver(pre_delete, sender=Page)
def log_page_pre_delete(sender, instance, **kwargs):
    log_action(instance.created_by.id, instance.created_by.username, "Page", instance.pk,
               "DELETED", timezone.now().isoformat())


# Обработчики сигналов для модели Task
@receiver(pre_save, sender=Task)
def log_task_pre_save(sender, instance, **kwargs):
    if instance.pk:
        log_action(instance.created_by.id, instance.created_by.username, "Task", instance.pk,
                   "UPDATED", timezone.now().isoformat())


@receiver(post_save, sender=Task)
def log_task_post_save(sender, instance, created, **kwargs):
    if created:
        log_action(instance.created_by.id, instance.created_by.username, "Task", instance.pk,
                   "CREATED", timezone.now().isoformat())


@receiver(pre_delete, sender=Task)
def log_task_pre_delete(sender, instance, **kwargs):
    log_action(instance.created_by.id, instance.created_by.username, "Task", instance.pk,
               "DELETED", timezone.now().isoformat())
