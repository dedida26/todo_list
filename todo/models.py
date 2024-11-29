from django.db import models
from django.contrib.auth.models import User


# Модель для реализации мягкого удаления.  Записи не удаляются физически из базы данных,
# а помечаются как удаленные с помощью поля `is_deleted`
class SoftDeletableModel(models.Model):
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):  # Переопределение метода delete() Django модели
        self.is_deleted = True  # Помечаем запись как удаленную
        self.save()


# Модель прав доступа к папке
class FolderPermission(models.Model):
    folder = models.ForeignKey('Folder', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    # Обеспечивает уникальность прав доступа для каждого пользователя в каждой папке
    class Meta:
        unique_together = ('folder', 'user')


# Модель прав доступа к странице
class PagePermission(models.Model):
    page = models.ForeignKey('Page', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    # Обеспечивает уникальность прав доступа для каждого пользователя для каждой странице
    class Meta:
        unique_together = ('page', 'user')


# Модель прав доступа к задачам
class TaskPermission(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    # Обеспечивает уникальность прав доступа для каждого пользователя дял каждой задачи
    class Meta:
        unique_together = ('task', 'user')


# Модель папки, использует мягкое удаление (SoftDeletableModel)
class Folder(SoftDeletableModel, models.Model):
    name = models.CharField(unique=True, max_length=50)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folder_owner')
    is_public = models.BooleanField(default=False)
    permissions = models.ManyToManyField(User, through='FolderPermission', blank=True,
                                         related_name='folder_permissions')

    def __str__(self):
        return self.name


# Модель страницы, использует мягкое удаление
class Page(SoftDeletableModel, models.Model):
    name = models.CharField(unique=True, max_length=50)
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_page')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_page')
    permissions = models.ManyToManyField(User, through='PagePermission', blank=True)

    def __str__(self):
        return self.name


# Модель задачи, использует мягкое удаление
class Task(SoftDeletableModel, models.Model):
    text = models.TextField(max_length=255)
    page = models.ForeignKey(Page, on_delete=models.SET_NULL, null=True)
    # Возможные статусы задачи
    STATUS_CHOICES = (
        ('DONE', 'Выполнено'),
        ('IN_PROGRESS', 'В процессе'),
        ('CANCELLED', 'Отменено'),
    )
    status = models.CharField(choices=STATUS_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_user')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_task')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_task')
    previous_version = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    permissions = models.ManyToManyField(User, through='TaskPermission', blank=True, related_name='task_permissions')

    def __str__(self):
        return self.text
