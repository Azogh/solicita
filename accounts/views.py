from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SolicitanteCadastroForm
from .models import Unidade

def registro_view(request):
    if request.method == 'POST':
        form = SolicitanteCadastroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Cadastro realizado com sucesso! Bem-vindo ao Solicita.")
            return redirect('dashboard')
    else:
        form = SolicitanteCadastroForm()
    return render(request, 'accounts/registro.html', {'form': form})

@login_required
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')

def buscar_unidades_view(request):
    regiao_id = request.GET.get('regiao_fiscal')
    unidades = Unidade.objects.filter(regiao_fiscal_id=regiao_id) if regiao_id else Unidade.objects.none()
    return render(request, 'accounts/partials/unidades_options.html', {'unidades': unidades})

def landing_page_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')