LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'todo_log.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'auth_log': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'general_log': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d %(message)s',
            'datefmt': '%d-%m-%Y %H:%M:%S',
        },
        'simple': {
            'format': '%(levelname)s %(message)s',
        },
    },
}
