import os.path
import unittest

import django
from django.conf import settings

from templatefinder import tests


def main():
    template_dirs = (
        os.path.join(os.path.dirname(__file__), 'templatefinder', 'test_project', 'templates'),
    )
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        INSTALLED_APPS=(
            'templatefinder.test_project.testapp',
        ),
        TEMPLATE_DIRS=template_dirs,
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': template_dirs,
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                ],
            },
        }]
    )
    if hasattr(django, 'setup'):
        django.setup()
    suite = unittest.TestLoader().loadTestsFromModule(tests)
    return suite
