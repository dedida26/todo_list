from django.db.models import Q
from rest_framework import viewsets, permissions, status
from .serializers import *
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .log_utils import log_read_action


# Миксин для логирования действий чтения данных
class ReadLoggingMixin:
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if response.status_code == 200:

            log_read_action(
                request.user.id,
                request.user.username,
                self.model._meta.model_name,
                kwargs.get('pk')
            )
        return response


# Миксин для реализации мягкого удаления объектов
class SoftDeletableViewSetMixin:

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FolderViewSet(SoftDeletableViewSetMixin, ReadLoggingMixin, viewsets.ModelViewSet):
    queryset = Folder.objects.filter(is_deleted=False)
    serializer_class = FolderSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    model = Folder

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, pk=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()

        for page in instance.page_set.all():
            page.is_deleted = True
            page.save()

        for task in Task.objects.filter(page__in=instance.page_set.all(), is_deleted=False):
            task.is_deleted = True
            task.save()

        return Response(
            status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Folder.objects.filter(
                Q(owner=user) |
                Q(permissions__in=[user]) |
                Q(is_public=True), is_deleted=False
            ).distinct()
        else:
            return Folder.objects.filter(is_public=True, is_deleted=False).distinct()


class PageViewSet(SoftDeletableViewSetMixin, ReadLoggingMixin, viewsets.ModelViewSet):
    queryset = Page.objects.filter(folder__is_deleted=False, is_deleted=False)
    serializer_class = PageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    model = Page

    def perform_create(self, serializer):
        folder = serializer.validated_data['folder']
        user = self.request.user

        if not (folder.owner == user or user in folder.permissions.all()):
            raise PermissionDenied(
                "У вас нет прав на создание страницы в этой папке.")
        serializer.save(created_by=user, updated_by=user)

    def get_queryset(self):
        user = self.request.user
        if user.has_perm('todo.view_page'):
            return Page.objects.filter(is_deleted=False)

        if user.is_authenticated:
            return Page.objects.filter(
                Q(folder__owner=user) |
                Q(folder__permissions__in=[user]) |
                Q(is_public=True)
            ).filter(is_deleted=False).distinct()
        else:
            return Page.objects.filter(is_public=True, is_deleted=False).distinct()


class TaskViewSet(SoftDeletableViewSetMixin, ReadLoggingMixin, viewsets.ModelViewSet):
    queryset = Task.objects.filter(page__is_deleted=False, is_deleted=False)
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    model = Task

    def perform_create(self, serializer):
        page_id = self.request.data.get('page')

        if not page_id:
            raise serializers.ValidationError({"page": "Требуется ID страницы"})

        try:
            page = Page.objects.get(pk=page_id)
        except Page.DoesNotExist:
            raise serializers.ValidationError({"page": "Страница не найдена"})

        user = self.request.user

        if not (
                page.folder.owner == user or
                user in page.folder.permissions.all() or
                page.is_public
        ):
            raise PermissionDenied("У вас нет прав на создание задачи на этой странице.")
        serializer.save(created_by=user, updated_by=user,
                        page=page)

    def get_queryset(self):
        user = self.request.user

        if user.has_perm('todo.view_task'):
            return Task.objects.filter(is_deleted=False)

        if user.is_authenticated:
            return Task.objects.filter(
                Q(page__folder__owner=user) |
                Q(page__folder__permissions__in=[user]) |
                Q(page__is_public=True)
            ).filter(is_deleted=False).distinct()
        else:
            return Task.objects.filter(page__is_public=True, is_deleted=False, page__is_deleted=False).distinct()


class FolderPermissionViewSet(viewsets.ModelViewSet):
    queryset = FolderPermission.objects.all()
    serializer_class = FolderPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(folder__owner=user)

    def perform_create(self, serializer):
        folder = serializer.validated_data.get('folder')
        user_to_grant = serializer.validated_data.get('user')
        if folder.owner != self.request.user:
            raise serializers.ValidationError(
                "Вы не можете назначать права для этой папки.")
        serializer.save()

    def perform_destroy(self, instance):
        folder = instance.folder

        if folder.owner != self.request.user:
            raise serializers.ValidationError(
                "Вы не можете удалить права для этой папки.")
        instance.delete()


class PagePermissionViewSet(viewsets.ModelViewSet):
    queryset = PagePermission.objects.all()
    serializer_class = PagePermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(
            Q(page__folder__owner=user) |
            Q(page__permissions__in=[user]) |
            Q(page__is_public=True)
        )

    def perform_create(self, serializer):
        page = serializer.validated_data.get('page')
        user_to_grant = serializer.validated_data.get('user')

        if not (page.folder.owner == self.request.user or self.request.user in page.folder.permissions.all()):
            raise serializers.ValidationError(
                "Вы не можете назначать права для этой страницы.")
        serializer.save()


class TaskPermissionViewSet(viewsets.ModelViewSet):
    queryset = TaskPermission.objects.all()
    serializer_class = TaskPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return TaskPermission.objects.filter(
            Q(task__page__folder__owner=user) |
            Q(task__page__permissions__in=[user]) |
            Q(task__page__is_public=True)
        ).distinct()

    def perform_create(self, serializer):
        task = serializer.validated_data.get('task')
        user_to_grant = serializer.validated_data.get('user')

        if task.page.folder.owner == self.request.user or self.request.user in task.page.folder.permissions.all():
            serializer.save()
        else:
            raise serializers.ValidationError("Вы не можете назначать права для этой задачи.")

