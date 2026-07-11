from django.contrib.auth.forms import AuthenticationForm


class StyledAuthenticationForm(AuthenticationForm):
    """Login form with the CSS hooks used by the project templates."""

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {
                'class': 'login-input',
                'placeholder': 'Usuario',
                'autocomplete': 'username',
                'autofocus': True,
            }
        )
        self.fields['password'].widget.attrs.update(
            {
                'class': 'login-input',
                'placeholder': 'Contrasena',
                'autocomplete': 'current-password',
            }
        )
