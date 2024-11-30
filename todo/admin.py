from django.contrib import admin
from .models import Folder, Page, Task, FolderPermission, PagePermission, TaskPermission

admin.site.register(Folder)
admin.site.register(Page)
admin.site.register(Task)
admin.site.register(FolderPermission)
admin.site.register(PagePermission)
admin.site.register(TaskPermission)
