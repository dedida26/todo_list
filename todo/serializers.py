from rest_framework import serializers
from .models import *
from django.urls import reverse


# Сериализатор для прав доступа к папкам
class FolderPermissionSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    folder = serializers.PrimaryKeyRelatedField(queryset=Folder.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = FolderPermission
        fields = ('id', 'folder', 'user', 'user_name', 'can_view', 'can_edit', 'can_delete')

    def get_user_name(self, obj):
        return obj.user.username


# Сериализатор для прав доступа к страницам
class PagePermissionSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    page = serializers.PrimaryKeyRelatedField(queryset=Page.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = PagePermission
        fields = ('id', 'page', 'user', 'user_name', 'can_view', 'can_edit', 'can_delete')

    # Вычисляет имя пользователя на основе объекта PagePermission.
    def get_user_name(self, obj):
        return obj.user.username


# Сериализатор для прав доступа к задачам
class TaskPermissionSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = TaskPermission
        fields = ('id', 'task', 'user', 'user_name', 'can_view', 'can_edit', 'can_delete')

    # Вычисляет имя пользователя на основе объекта PagePermission.
    def get_user_name(self, obj):
        return obj.user.username


# Сериализатор для папок
class FolderSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100)
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = ('id', 'name', 'owner', 'owner_name', 'is_public')
        extra_kwargs = {
            'owner': {'read_only': True},
            'owner_name': {'read_only': True}
        }

    # Вычисляет и возвращает имя пользователя, являющегося владельцем папки
    def get_owner_name(self, obj):
        return obj.owner.username


# Сериализатор для страниц
class PageSerializer(serializers.ModelSerializer):
    folder = serializers.PrimaryKeyRelatedField(queryset=Folder.objects.filter(is_deleted=False))
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    folder_data = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True, format='%d-%m-%Y %H:%M:%S')
    updated_at = serializers.DateTimeField(read_only=True, format='%d-%m-%Y %H:%M:%S')

    class Meta:
        model = Page
        fields = ('id', 'name', 'folder', 'folder_data', 'is_public', 'created_at', 'updated_at', 'created_by',
                  'updated_by')
        extra_kwargs = {
            'name': {'required': True},
            'folder': {'required': True}
        }

    # Возвращает сериализованные данные о папке страницы, используя FolderSerializer.
    def get_folder_data(self, obj):
        folder_serializer = FolderSerializer(instance=obj.folder)
        return folder_serializer.data


# Сериализатор для задач
class TaskSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True, format='%d-%m-%Y %H:%M:%S')
    updated_at = serializers.DateTimeField(read_only=True, format='%d-%m-%Y %H:%M:%S')
    page = serializers.PrimaryKeyRelatedField(queryset=Page.objects.filter(is_deleted=False))
    user_name = serializers.SerializerMethodField()
    previous_version_url = serializers.SerializerMethodField()
    page_name = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ('id', 'text', 'status', 'user', 'user_name', 'page', 'page_name', 'previous_version',
                  'previous_version_url', 'created_at', 'updated_at', 'created_by',
                  'updated_by')
        extra_kwargs = {
            'text': {'required': True},
            'page': {'required': True}
        }

    # Возвращает имя страницы, связанной с задачей
    def get_page_name(self, obj):
        return obj.page.name

    # Возвращает имя пользователя, связанного с задачей
    def get_user_name(self, obj):
        return obj.user.username

    # Генерирует URL для предыдущей версии задачи, если она существует
    def get_previous_version_url(self, obj):
        if obj.previous_version:
            return reverse('task-detail', args=[obj.previous_version.id])
        return None
