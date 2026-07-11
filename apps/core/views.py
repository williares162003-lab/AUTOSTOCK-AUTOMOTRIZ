from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    role = 'Administrador' if request.user.is_superuser else 'Operador de almacen'
    context = {
        'role': role,
        'summary_cards': [
            {'label': 'Productos registrados', 'value': '0'},
            {'label': 'Entradas del mes', 'value': '0'},
            {'label': 'Salidas del mes', 'value': '0'},
            {'label': 'Alertas de stock', 'value': '0'},
        ],
    }
    return render(request, 'core/dashboard.html', context)

# Create your views here.
