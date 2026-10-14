from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import OrdemServico, FeedbackDMR
from .forms import OrdemServicoForm, GestorAnaliseForm, FeedbackDMRForm
from accounts.models import Usuario


def notificar_gestores_por_email(os_item, request):
    """ Busca todos os gestores vinculados à unidade da OS e envia notificação """
    gestores = Usuario.objects.filter(
        perfil=Usuario.PerfilChoices.GESTOR,
        unidades_gerenciadas=os_item.unidade,
        is_active=True
    ).values_list('email', flat=True)

    if gestores:
        assunto = f"[Solicita] Nova Ordem de Serviço {os_item.numero_os} - {os_item.unidade.sigla}"
        link_os = request.build_absolute_uri(f"/os/{os_item.pk}/")
        
        mensagem = (
            f"Olá, Gestor!\n\n"
            f"Uma nova Ordem de Serviço foi enviada e aguarda sua análise:\n\n"
            f"• Código: {os_item.numero_os}\n"
            f"• Unidade: {os_item.unidade.nome} ({os_item.unidade.sigla})\n"
            f"• Solicitante: {os_item.solicitante.get_full_name()}\n"
            f"• Assunto: {os_item.assunto}\n"
            f"• Prioridade: {os_item.get_prioridade_display()}\n\n"
            f"Para visualizar e gerenciar este chamado, acesse o link:\n"
            f"{link_os}\n\n"
            f"Atenciosamente,\n"
            f"Sistema Solicita - RFB"
        )
        
        try:
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'solicita@rfb.gov.br'),
                recipient_list=list(gestores),
                fail_silently=True
            )
        except Exception as e:
            print(f"Erro ao enviar e-mail de notificação: {e}")


@login_required
def criar_os_view(request):
    if not request.user.unidade:
        messages.error(
            request, 
            "Seu usuário não possui uma Unidade/Repartição vinculada ao cadastro. "
            "Atualize sua lotação no perfil ou solicite ao administrador."
        )
        return redirect('perfil')

    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            os_item = form.save(commit=False)
            os_item.solicitante = request.user
            os_item.unidade = request.user.unidade
            
            if 'btn_enviar' in request.POST:
                os_item.status = OrdemServico.StatusChoices.ENVIADO
                os_item.enviado_em = timezone.now()
                os_item.save()
                
                notificar_gestores_por_email(os_item, request)
                messages.success(request, f"Ordem de Serviço {os_item.numero_os} enviada com sucesso!")
            else:
                os_item.status = OrdemServico.StatusChoices.RASCUNHO
                os_item.save()
                messages.info(request, f"Rascunho da OS {os_item.numero_os} salvo com sucesso.")
            
            return redirect('dashboard')
    else:
        form = OrdemServicoForm(user=request.user)
    
    return render(request, 'solicitacoes/criar_os.html', {'form': form})


@login_required
def editar_os_view(request, pk):
    os_item = get_object_or_404(OrdemServico, pk=pk, solicitante=request.user)
    
    if os_item.status != OrdemServico.StatusChoices.RASCUNHO:
        messages.error(request, "Esta Ordem de Serviço já foi enviada ao Gestor e não pode ser alterada.")
        return redirect('detalhar_os', pk=os_item.pk)

    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, request.FILES, instance=os_item, user=request.user)
        if form.is_valid():
            os_updated = form.save(commit=False)
            if 'btn_enviar' in request.POST:
                os_updated.status = OrdemServico.StatusChoices.ENVIADO
                os_updated.enviado_em = timezone.now()
                os_updated.save()
                
                notificar_gestores_por_email(os_updated, request)
                messages.success(request, f"Ordem de Serviço {os_updated.numero_os} enviada com sucesso!")
            else:
                os_updated.save()
                messages.info(request, "Rascunho atualizado com sucesso.")
            
            return redirect('dashboard')
    else:
        form = OrdemServicoForm(instance=os_item, user=request.user)

    return render(request, 'solicitacoes/editar_os.html', {'form': form, 'os_item': os_item})


@login_required
def detalhar_os_view(request, pk):
    os_item = get_object_or_404(OrdemServico, pk=pk)
    return render(request, 'solicitacoes/detalhar_os.html', {'os_item': os_item})


@login_required
def analisar_os_gestor_view(request, pk):
    os_item = get_object_or_404(OrdemServico, pk=pk)
    
    if request.user.perfil != Usuario.PerfilChoices.GESTOR or not request.user.unidades_gerenciadas.filter(id=os_item.unidade.id).exists():
        messages.error(request, "Você não tem permissão para analisar solicitações desta unidade.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = GestorAnaliseForm(request.POST, instance=os_item)
        if form.is_valid():
            os_updated = form.save(commit=False)
            
            if os_updated.status == OrdemServico.StatusChoices.EM_ATENDIMENTO:
                os_updated.agendado_em = timezone.now()
            elif os_updated.status == OrdemServico.StatusChoices.CONCLUIDO:
                os_updated.concluido_em = timezone.now()

            os_updated.save()

            if os_updated.solicitante.email:
                try:
                    assunto = f"[Solicita] Atualização na OS {os_updated.numero_os} - {os_updated.get_status_display()}"
                    msg = (
                        f"Olá, {os_updated.solicitante.first_name}!\n\n"
                        f"Sua Ordem de Serviço foi atualizada pelo Gestor Regional:\n\n"
                        f"• Código: {os_updated.numero_os}\n"
                        f"• Novo Status: {os_updated.get_status_display()}\n"
                        f"• Data Prevista de Atendimento: {os_updated.data_prevista_atendimento.strftime('%d/%m/%Y') if os_updated.data_prevista_atendimento else 'Não informada'}\n\n"
                        f"Parecer Técnico:\n{os_updated.parecer_gestor or 'Sem observações.'}\n\n"
                        f"Acesse o Solicita para acompanhar os detalhes."
                    )
                    send_mail(
                        subject=assunto,
                        message=msg,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'solicita@rfb.gov.br'),
                        recipient_list=[os_updated.solicitante.email],
                        fail_silently=True
                    )
                except Exception as e:
                    print(f"Erro ao notificar solicitante: {e}")

            messages.success(request, f"Ordem de Serviço {os_updated.numero_os} atualizada com sucesso!")
            return redirect('dashboard')
    else:
        form = GestorAnaliseForm(instance=os_item)

    return render(request, 'solicitacoes/analisar_os.html', {'form': form, 'os_item': os_item})


@login_required
def cronograma_visitas_view(request):
    user = request.user
    if user.perfil != Usuario.PerfilChoices.GESTOR:
        messages.error(request, "Apenas gestores têm acesso ao cronograma de visitas.")
        return redirect('dashboard')

    unidades_ids = user.unidades_gerenciadas.values_list('id', flat=True)
    
    if request.method == 'POST' and 'btn_alocar' in request.POST:
        os_id = request.POST.get('os_id')
        data_agendada_raw = request.POST.get('data_prevista')
        
        if os_id and data_agendada_raw:
            try:
                if '/' in data_agendada_raw:
                    dia, mes, ano = data_agendada_raw.split('/')
                    data_agendada = f"{ano}-{mes}-{dia}"
                else:
                    data_agendada = data_agendada_raw

                os_target = get_object_or_404(OrdemServico, pk=os_id, unidade_id__in=unidades_ids)
                os_target.data_prevista_atendimento = data_agendada
                os_target.status = OrdemServico.StatusChoices.EM_ATENDIMENTO
                os_target.agendado_em = timezone.now()
                os_target.save()
                
                messages.success(request, f"OS {os_target.numero_os} alocada com sucesso!")
                return redirect('cronograma_visitas')
            except ValueError:
                messages.error(request, "Formato de data inválido. Use dd/mm/aaaa.")

    os_pendentes = OrdemServico.objects.filter(
        unidade_id__in=unidades_ids,
        status=OrdemServico.StatusChoices.ENVIADO,
        data_prevista_atendimento__isnull=True
    ).order_by('-prioridade', 'criado_em')

    os_agendadas = OrdemServico.objects.filter(
        unidade_id__in=unidades_ids,
        status=OrdemServico.StatusChoices.EM_ATENDIMENTO,
        data_prevista_atendimento__isnull=False
    ).order_by('data_prevista_atendimento')

    hoje = date.today()
    dias_grade = []
    for i in range(14):
        dia_corrente = hoje + timedelta(days=i)
        if dia_corrente.weekday() < 5:
            os_no_dia = os_agendadas.filter(data_prevista_atendimento=dia_corrente)
            dias_grade.append({
                'data': dia_corrente,
                'dia_semana': dia_corrente.strftime('%A'),
                'os_list': os_no_dia
            })

    tem_urgente_pendente = os_pendentes.filter(prioridade=OrdemServico.PrioridadeChoices.ALTA).exists()

    context = {
        'os_pendentes': os_pendentes,
        'dias_grade': dias_grade,
        'tem_urgente_pendente': tem_urgente_pendente,
    }
    return render(request, 'solicitacoes/cronograma.html', context)


@login_required
def criar_feedback_dmr_view(request, os_id=None):
    os_item = None
    if os_id:
        os_item = get_object_or_404(OrdemServico, pk=os_id)

    if request.method == 'POST':
        form = FeedbackDMRForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.autor = request.user
            feedback.unidade = request.user.unidade
            if os_item and not feedback.ordem_servico:
                feedback.ordem_servico = os_item
            feedback.save()
            
            messages.success(request, "Feedback de DMR registrado com sucesso!")
            return redirect('dashboard')
    else:
        initial_data = {}
        if os_item:
            initial_data['ordem_servico'] = os_item.pk
        form = FeedbackDMRForm(user=request.user, initial=initial_data)

    return render(request, 'solicitacoes/criar_feedback_dmr.html', {
        'form': form,
        'os_item': os_item
    })


@login_required
def listar_feedbacks_dmr_view(request):
    if request.user.perfil != Usuario.PerfilChoices.GESTOR:
        messages.error(request, "Acesso restrito a gestores.")
        return redirect('dashboard')

    unidades_ids = request.user.unidades_gerenciadas.values_list('id', flat=True)
    feedbacks = FeedbackDMR.objects.filter(unidade_id__in=unidades_ids)

    return render(request, 'solicitacoes/listar_feedbacks_dmr.html', {
        'feedbacks': feedbacks
    })