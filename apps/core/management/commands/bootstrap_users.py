import os
import secrets
import string

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


def generate_password(length=16):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = 'Create or update the initial admin and warehouse operator users.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-username',
            default=os.environ.get('DJANGO_ADMIN_USERNAME', 'admin'),
        )
        parser.add_argument(
            '--admin-email',
            default=os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@example.com'),
        )
        parser.add_argument(
            '--admin-password',
            default=os.environ.get('DJANGO_ADMIN_PASSWORD'),
        )
        parser.add_argument(
            '--operator-username',
            default=os.environ.get('DJANGO_OPERATOR_USERNAME', 'almacen'),
        )
        parser.add_argument(
            '--operator-email',
            default=os.environ.get('DJANGO_OPERATOR_EMAIL', 'almacen@example.com'),
        )
        parser.add_argument(
            '--operator-password',
            default=os.environ.get('DJANGO_OPERATOR_PASSWORD'),
        )

    def handle(self, *args, **options):
        operator_group, _ = Group.objects.get_or_create(name='Almacenero')

        admin_created, admin_password = self.sync_user(
            username=options['admin_username'],
            email=options['admin_email'],
            password=options['admin_password'],
            is_staff=True,
            is_superuser=True,
        )
        operator_created, operator_password = self.sync_user(
            username=options['operator_username'],
            email=options['operator_email'],
            password=options['operator_password'],
            is_staff=False,
            is_superuser=False,
            group=operator_group,
        )

        self.stdout.write(self.style.SUCCESS('Usuarios iniciales listos.'))
        self.print_result('Admin', options['admin_username'], admin_created, admin_password)
        self.print_result(
            'Operador',
            options['operator_username'],
            operator_created,
            operator_password,
        )

    def sync_user(self, username, email, password, is_staff, is_superuser, group=None):
        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)
        generated_password = None

        user.email = email
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.is_active = True

        if password:
            user.set_password(password)
        elif created:
            generated_password = generate_password()
            user.set_password(generated_password)

        user.save()

        if group:
            user.groups.add(group)

        return created, generated_password

    def print_result(self, label, username, created, generated_password):
        status = 'creado' if created else 'actualizado'
        self.stdout.write(f'{label}: {username} ({status})')
        if generated_password:
            self.stdout.write(f'  Contrasena generada: {generated_password}')
        else:
            self.stdout.write('  Contrasena: definida por parametro/env o sin cambios')
