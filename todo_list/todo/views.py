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


# Представление для работы с папками, использует миксины для мягкого удаления и логирования
class FolderViewSet(SoftDeletableViewSetMixin, ReadLoggingMixin, viewsets.ModelViewSet):
    queryset = Folder.objects.filter(is_deleted=False)
    serializer_class = FolderSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    model = Folder

    # Переопределённый метод для получения объекта папки. Добавлена проверка прав доступа
    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, pk=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj

    # Переопределённый метод destroy для реализации каскадного мягкого удаления связанных страниц и задач
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()

        # Каскадное мягкое удаление связанных страниц
        for page in instance.page_set.all():
            page.is_deleted = True
            page.save()

        # Каскадное мягкое удаление связанных задач (только тех, что не помечены как удалённые
        for task in Task.objects.filter(page__in=instance.page_set.all(), is_deleted=False):
            task.is_deleted = True
            task.save()

        return Response(
            status=status.HTTP_204_NO_CONTENT)

    # Переопределяем метод perform_create для автоматического задания владельца папки
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # Переопределяем метод get_queryset для фильтрации папок в зависимости от авторизации пользователя
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:  # Если пользователь авторизован
            # Возвращаем папки, принадлежащие пользователю, либо папки, к которым у него есть доступ,
            # либо публичные папки
            return Folder.objects.filter(
                #  Q - сложный запрос к БД("И", "ИЛИ", "НЕТ"), а "|" это "ИЛИ"
                Q(owner=user) |  # Папка принадлежит пользователю
                Q(permissions__in=[user]) |  # Пользователь имеет доступ к папке
                Q(is_public=True), is_deleted=False  # Страница публичная и не удалена
            ).distinct()
        else:  # Если пользователь не авторизован
            # Возвращаем только публичные папки
            return Folder.objects.filter(is_public=True, is_deleted=False).distinct()


# Представление дла работы со страницами, использует миксины для мягкого удаления и логирования
class PageViewSet(SoftDeletableViewSetMixin, ReadLoggingMixin, viewsets.ModelViewSet):
    queryset = Page.objects.filter(folder__is_deleted=False, is_deleted=False)
    serializer_class = PageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    model = Page

    # Переопределяем метод perform_create для проверки прав доступа перед созданием страницы
    def perform_create(self, serializer):
        folder = serializer.validated_data['folder']
        user = self.request.user

        # Проверка, имеет ли пользователь права на создание страницы в данной папке
        if not (folder.owner == user or user in folder.permissions.all()):  # Проверка владения папкой или
            # наличия прав доступа
            raise PermissionDenied(
                "У вас нет прав на создание страницы в этой папке.")
        serializer.save(created_by=user, updated_by=user)

    # Переопределяем метод get_queryset для фильтрации страниц в зависимости от прав доступа пользователя
    def get_queryset(self):
        user = self.request.user
        if user.has_perm('todo.view_page'):
            return Page.objects.filter(is_deleted=False)

        if user.is_authenticated:
            # Возвращаем страницы, удовлетворяющие одному из условий:
            # 1. Страница находится в папке, владельцем которой является пользователь
            # 2. Пользователь имеет права доступа к папке, в которой находится страница
            # 3. Страница является публичной
            return Page.objects.filter(
                Q(folder__owner=user) |  # Папка принадлежит пользователю
                Q(folder__permissions__in=[user]) |  # Пользователь имеет доступ к папке
                Q(is_public=True)  # Страница публичная
            ).filter(is_deleted=False).distinct()
        else:  # Если пользователь не авторизован
            # Возвращаем только публичные страницы, не помеченные как удалённые
            return Page.objects.filter(is_public=True, is_deleted=False).distinct()


# Представление дла работы с задачами, использует миксины для мягкого удаления и логирования
class TaskViewSet(SoftDeletableViewSetMixin, ReadLoggingMixin, viewsets.ModelViewSet):
    queryset = Task.objects.filter(page__is_deleted=False, is_deleted=False)
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    model = Task

    # Переопределяем метод perform_create для проверки прав доступа и связывания задачи со страницей перед созданием
    def perform_create(self, serializer):
        page_id = self.request.data.get('page')

        # Проверка наличия ID страницы
        if not page_id:  # Если ID страницы не указан
            raise serializers.ValidationError({"page": "Требуется ID страницы"})  # Выбрасываем ошибку валидации

        try:
            page = Page.objects.get(pk=page_id)  # Получаем объект страницы по ID
        except Page.DoesNotExist:
            raise serializers.ValidationError({"page": "Страница не найдена"})  # Выбрасываем ошибку валидации, если
            # страница не найдена

        user = self.request.user

        # Проверка прав доступа пользователя к странице
        if not (
                page.folder.owner == user or
                user in page.folder.permissions.all() or
                page.is_public
        ):  # Проверяем владение папкой, права доступа к папке или публичность страницы
            raise PermissionDenied("У вас нет прав на создание задачи на этой странице.")
        serializer.save(created_by=user, updated_by=user,
                        page=page)  # Сохраняем задачу, устанавливая создателя, редактора и связывая её со страницей

    # Переопределяем метод get_queryset для фильтрации задач в зависимости от прав доступа пользователя
    def get_queryset(self):
        user = self.request.user

        if user.has_perm('todo.view_task'):
            return Task.objects.filter(is_deleted=False)

        if user.is_authenticated:
            # Возвращаем задачи, удовлетворяющие одному из условий:
            # 1. Задача находится на странице в папке, владельцем которой является пользователь
            # 2. Задача находится на странице в папке, к которой пользователь имеет доступ
            # 3. Задача находится на публичной странице
            return Task.objects.filter(
                Q(page__folder__owner=user) |  # Папка страницы принадлежит пользователю
                Q(page__folder__permissions__in=[user]) |  # Пользователь имеет доступ к папке страницы
                Q(page__is_public=True)  # Страница публичная
            ).filter(is_deleted=False).distinct()
        else:  # Если пользователь не авторизован
            # Возвращаем только задачи на публичных страницах, не помеченные как удалённые
            return Task.objects.filter(page__is_public=True, is_deleted=False, page__is_deleted=False).distinct()


# Представление для управления правами доступа к папкам
class FolderPermissionViewSet(viewsets.ModelViewSet):
    queryset = FolderPermission.objects.all()
    serializer_class = FolderPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Переопределяем метод get_queryset для фильтрации прав доступа, доступных только владельцу папки
    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(folder__owner=user)

    # Переопределяем метод perform_create для проверки прав доступа перед созданием записи о правах доступа
    def perform_create(self, serializer):
        folder = serializer.validated_data.get('folder')
        user_to_grant = serializer.validated_data.get('user')
        if folder.owner != self.request.user:
            raise serializers.ValidationError(
                "Вы не можете назначать права для этой папки.")
        serializer.save()

    # Переопределяем метод perform_destroy для проверки прав доступа перед удалением записи о правах доступа
    def perform_destroy(self, instance):
        folder = instance.folder

        if folder.owner != self.request.user:  # Проверяем, является ли текущий пользователь владельцем папки
            raise serializers.ValidationError(
                "Вы не можете удалить права для этой папки.")
        instance.delete()


# Представление для управления правами доступа к страницам
class PagePermissionViewSet(viewsets.ModelViewSet):
    queryset = PagePermission.objects.all()
    serializer_class = PagePermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Переопределяем метод get_queryset для фильтрации прав доступа, доступных текущему пользователю
    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(
            Q(page__folder__owner=user) |  # Права доступа к страницам в папках, принадлежащих текущему пользователю
            Q(page__permissions__in=[user]) |  # Права доступа к страницам, к которым пользователь имеет прямой доступ
            Q(page__is_public=True)  # Права доступа к публичным страницам
        )

    # Переопределяем метод perform_create для проверки прав доступа перед созданием записи о правах доступа
    def perform_create(self, serializer):
        page = serializer.validated_data.get('page')
        user_to_grant = serializer.validated_data.get('user')

        if not (page.folder.owner == self.request.user or self.request.user in page.folder.permissions.all()):
            raise serializers.ValidationError(
                "Вы не можете назначать права для этой страницы.")
        serializer.save()


# Представление для управления правами доступа к задачам
class TaskPermissionViewSet(viewsets.ModelViewSet):
    queryset = TaskPermission.objects.all()
    serializer_class = TaskPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Переопределяем метод get_queryset для эффективной фильтрации прав доступа, доступных текущему пользователю
    def get_queryset(self):
        user = self.request.user
        return TaskPermission.objects.filter(
            Q(task__page__folder__owner=user) |  # Права доступа к задачам в папках, принадлежащих пользователю
            Q(task__page__permissions__in=[user]) |  # Права доступа к задачам на страницах, к которым пользователь
            # имеет прямой доступ
            Q(task__page__is_public=True)  # Права доступа к задачам на публичных страницах
        ).distinct()

    # Переопределяем метод perform_create для проверки прав доступа перед созданием записи о правах доступа
    def perform_create(self, serializer):
        task = serializer.validated_data.get('task')
        user_to_grant = serializer.validated_data.get('user')

        # Проверка прав доступа: текущий пользователь должен быть владельцем папки страницы задачи или иметь права
        # доступа к этой папке
        if task.page.folder.owner == self.request.user or self.request.user in task.page.folder.permissions.all():
            serializer.save()
        else:
            raise serializers.ValidationError("Вы не можете назначать права для этой задачи.")

