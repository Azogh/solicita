from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
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

    # Rota para GESTOR
    if user.perfil == Usuario.PerfilChoices.GESTOR:
        unidades_gerenciadas = user.unidades_gerenciadas.all()
        solicitacoes = OrdemServico.objects.filter(
            unidade__in=unidades_gerenciadas
        ).order_by('-criado_em')

        # Aplicar Filtros Rápido do Gestor
        busca = request.GET.get('busca')
        status_filtro = request.GET.get('status')

        if busca:
            solicitacoes = solicitacoes.filter(
                assunto__icontains=busca
            ) | solicitacoes.filter(
                numero_os__icontains=busca
            )

        if status_filtro:
            solicitacoes = solicitacoes.filter(status=status_filtro)

        total_pendentes = solicitacoes.filter(status=OrdemServico.StatusChoices.ENVIADO).count()
        total_agendadas = solicitacoes.filter(status=OrdemServico.StatusChoices.EM_ATENDIMENTO).count()
        total_concluidas = solicitacoes.filter(status=OrdemServico.StatusChoices.CONCLUIDO).count()

        context = {
            'solicitacoes': solicitacoes,
            'total_pendentes': total_pendentes,
            'total_agendadas': total_agendadas,
            'total_concluidas': total_concluidas,
        }
        return render(request, 'dashboard_gestor.html', context)

    # Rota para SOLICITANTE (Mostra todas as OSs da Unidade do usuário)
    else:
        if user.unidade:
            solicitacoes = OrdemServico.objects.filter(unidade=user.unidade).order_by('-criado_em')
        else:
            solicitacoes = OrdemServico.objects.filter(solicitante=user).order_by('-criado_em')

        # Aplicar Filtros do Solicitante
        busca = request.GET.get('busca')
        status_filtro = request.GET.get('status')
        data_inicio = request.GET.get('data_inicio')

        if busca:
            solicitacoes = solicitacoes.filter(
                assunto__icontains=busca
            ) | solicitacoes.filter(
                numero_os__icontains=busca
            )

        if status_filtro:
            solicitacoes = solicitacoes.filter(status=status_filtro)

        if data_inicio:
            try:
                if '/' in data_inicio:
                    d, m, a = data_inicio.split('/')
                    dt_converted = f"{a}-{m}-{d}"
                else:
                    dt_converted = data_inicio
                solicitacoes = solicitacoes.filter(criado_em__date>=dt_converted)
            except ValueError:
                pass

        total_rascunhos = solicitacoes.filter(status=OrdemServico.StatusChoices.RASCUNHO).count()
        total_andamento = solicitacoes.filter(
            status__in=[OrdemServico.StatusChoices.ENVIADO, OrdemServico.StatusChoices.EM_ATENDIMENTO]
        ).count()
        total_concluidas = solicitacoes.filter(status=OrdemServico.StatusChoices.CONCLUIDO).count()

        context = {
            'solicitacoes': solicitacoes,
            'total_rascunhos': total_rascunhos,
            'total_andamento': total_andamento,
            'total_concluidas': total_concluidas,
        }
        return render(request, 'dashboard_solicitante.html', context)


@login_required
def perfil_view(request):
    email_suporte = getattr(settings, 'ADMIN_CONTACT_EMAIL', 'andre-gustavo.ozga@rfb.gov.br')
    
    if request.method == 'POST':
        if 'btn_salvar_perfil' in request.POST:
            form_perfil = PerfilEditarForm(request.POST, instance=request.user)
            form_senha = PasswordChangeForm(user=request.user)
            if form_perfil.is_valid():
                form_perfil.save()
                messages.success(request, "Seu telefone/WhatsApp foi atualizado com sucesso!")
                return redirect('perfil')
        elif 'btn_alterar_senha' in request.POST:
            form_perfil = PerfilEditarForm(instance=request.user)
            form_senha = PasswordChangeForm(user=request.user, data=request.POST)
            if form_senha.is_valid():
                user = form_senha.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Sua senha foi alterada com sucesso!")
                return redirect('perfil')
            else:
                messages.error(request, "Por favor, corrija os erros no formulário de senha abaixo.")
    else:
        form_perfil = PerfilEditarForm(instance=request.user)
        form_senha = PasswordChangeForm(user=request.user)

    return render(request, 'accounts/perfil.html', {
        'form': form_perfil,
        'form_senha': form_senha,
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