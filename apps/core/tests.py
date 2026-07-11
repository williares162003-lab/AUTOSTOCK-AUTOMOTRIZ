from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse


class LoginFlowTests(TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_user_can_log_in_and_reach_dashboard(self):
        User = get_user_model()
        User.objects.create_user(username='almacen', password='StrongPass123')

        response = self.client.post(
            reverse('login'),
            {'username': 'almacen', 'password': 'StrongPass123'},
        )

        self.assertRedirects(response, reverse('dashboard'))


class BootstrapUsersCommandTests(TestCase):
    def test_command_creates_admin_and_operator(self):
        output = StringIO()

        call_command(
            'bootstrap_users',
            admin_password='AdminPass123',
            operator_password='OperatorPass123',
            stdout=output,
        )

        User = get_user_model()
        admin = User.objects.get(username='admin')
        operator = User.objects.get(username='almacen')

        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertFalse(operator.is_superuser)
        self.assertFalse(operator.is_staff)
        self.assertTrue(Group.objects.filter(name='Almacenero', user=operator).exists())
        self.assertIn('Usuarios iniciales listos', output.getvalue())

# Create your tests here.
