from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .forms import StyledAuthenticationForm
from . import views

urlpatterns = [
    path('', views.panel, name='panel'),
    path(
        'login/',
        LoginView.as_view(
            authentication_form=StyledAuthenticationForm,
            redirect_authenticated_user=True,
            template_name='login.html',
        ),
        name='login',
    ),
    path('logout/', LogoutView.as_view(), name='logout'),
]
