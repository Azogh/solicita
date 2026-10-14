from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .forms import SolicitanteCadastroForm, PerfilEditarForm
from .models import Unidade, Usuario, RegiaoFiscal
from solicitacoes.models import OrdemServico

def landing_page_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')

def registro_view(request):
    if request.method == 'POST':
        form = SolicitanteCadastroForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.perfil == Usuario.PerfilChoices.GESTOR:
                email_suporte = getattr(settings, 'ADMIN_CONTACT_EMAIL', 'andre-gustavo.ozga@rfb.gov.br')
                messages.warning(
                    request, 
                    f"Cadastro de Gestor realizado com sucesso! Sua conta está aguardando validação do administrador. "
                    f"Para agilizar a liberação, entre em contato via Teams ou e-mail institucional: {email_suporte}."
                )
                return redirect('login')
            else:
                login(request, user)
                messages.success(request, "Cadastro realizado com sucesso! Bem-vindo ao Solicita.")
                return redirect('dashboard')
    else:
        form = SolicitanteCadastroForm()
    return render(request, 'accounts/registro.html', {'form': form})

@login_required
def dashboard_view(request):
    user = request.user
    if user.perfil == Usuario.PerfilChoices.GESTOR:
        unidades_ids = user.unidades_gerenciadas.values_list('id', flat=True)
        solicitacoes = OrdemServico.objects.filter(unidade_id__in=unidades_ids)
        context = {
            'total_pendentes': solicitacoes.filter(status=OrdemServico.StatusChoices.ENVIADO).count(),
            'total_atendimento': solicitacoes.filter(status=OrdemServico.StatusChoices.EM_ATENDIMENTO).count(),
            'total_concluidas': solicitacoes.filter(status=OrdemServico.StatusChoices.CONCLUIDO).count(),
            'solicitacoes': solicitacoes[:10]
        }
        return render(request, 'dashboard_gestor.html', context)
    else:
        minhas_os = OrdemServico.objects.filter(solicitante=user)
        context = {
            'rascunhos_count': minhas_os.filter(status=OrdemServico.StatusChoices.RASCUNHO).count(),
            'em_andamento_count': minhas_os.filter(status__in=[OrdemServico.StatusChoices.ENVIADO, OrdemServico.StatusChoices.EM_ATENDIMENTO]).count(),
            'concluidas_count': minhas_os.filter(status=OrdemServico.StatusChoices.CONCLUIDO).count(),
            'solicitacoes_recentes': minhas_os[:10]
        }
        return render(request, 'dashboard_solicitante.html', context)

@login_required
def perfil_view(request):
    if request.method == 'POST':
        form = PerfilEditarForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Seu telefone/WhatsApp foi atualizado com sucesso!")
            return redirect('perfil')
    else:
        form = PerfilEditarForm(instance=request.user)
    
    email_suporte = getattr(settings, 'ADMIN_CONTACT_EMAIL', 'andre-gustavo.ozga@rfb.gov.br')
    return render(request, 'accounts/perfil.html', {
        'form': form,
        'email_suporte': email_suporte
    })

@login_required
def solicitar_elevacao_gestor_view(request):
    email_suporte = getattr(settings, 'ADMIN_CONTACT_EMAIL', 'andre-gustavo.ozga@rfb.gov.br')
    messages.info(
        request, 
        f"Sua solicitação de alteração para Gestor foi registrada. Por favor, envie uma mensagem no Teams ou e-mail para {email_suporte} para homologação."
    )
    return redirect('perfil')

def buscar_unidades_view(request):
    regiao_id = request.GET.get('regiao_fiscal')
    unidades = Unidade.objects.filter(regiao_fiscal_id=regiao_id) if regiao_id else Unidade.objects.none()
    return render(request, 'accounts/partials/unidades_options.html', {'unidades': unidades})

def buscar_unidades_checkbox_view(request):
    regiao_id = request.GET.get('regiao_fiscal')
    unidades = Unidade.objects.filter(regiao_fiscal_id=regiao_id) if regiao_id else Unidade.objects.none()
    return render(request, 'accounts/partials/unidades_checkboxes.html', {'unidades': unidades})