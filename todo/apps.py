from django.apps import AppConfig


class TodoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'todo'

    def ready(self):
        import todo.auth_log
        import todo.log_utils
