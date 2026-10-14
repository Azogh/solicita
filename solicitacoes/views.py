from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import OrdemServico
from .forms import OrdemServicoForm, GestorAnaliseForm
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
                fail_silently=True  # Não quebra a tela se o servidor de e-mail falhar
            )
        except Exception as e:
            print(f"Erro ao enviar e-mail de notificação: {e}")

@login_required
def criar_os_view(request):
    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, user=request.user)
        if form.is_valid():
            os_item = form.save(commit=False)
            os_item.solicitante = request.user
            os_item.unidade = request.user.unidade
            
            if 'btn_enviar' in request.POST:
                os_item.status = OrdemServico.StatusChoices.ENVIADO
                os_item.enviado_em = timezone.now()
                os_item.save()
                
                # Dispara notificação por e-mail para os gestores
                notificar_gestores_por_email(os_item, request)
                
                messages.success(request, f"Ordem de Serviço {os_item.numero_os} enviada com sucesso! Gestores notificados por e-mail.")
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
        form = OrdemServicoForm(request.POST, instance=os_item, user=request.user)
        if form.is_valid():
            os_updated = form.save(commit=False)
            if 'btn_enviar' in request.POST:
                os_updated.status = OrdemServico.StatusChoices.ENVIADO
                os_updated.enviado_em = timezone.now()
                os_updated.save()
                
                # Dispara notificação ao enviar o rascunho
                notificar_gestores_por_email(os_updated, request)
                
                messages.success(request, f"Ordem de Serviço {os_updated.numero_os} enviada com sucesso! Gestores notificados por e-mail.")
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
    
    # Trava de segurança: apenas gestores com permissão na unidade podem analisar
    if request.user.perfil != Usuario.PerfilChoices.GESTOR or not request.user.unidades_gerenciadas.filter(id=os_item.unidade.id).exists():
        messages.error(request, "Você não tem permissão para analisar solicitações desta unidade.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = GestorAnaliseForm(request.POST, instance=os_item)
        if form.is_valid():
            os_updated = form.save(commit=False)
            
            # Se foi agendado para atendimento
            if os_updated.status == OrdemServico.StatusChoices.EM_ATENDIMENTO:
                os_updated.agendado_em = timezone.now()
            elif os_updated.status == OrdemServico.StatusChoices.CONCLUIDO:
                os_updated.concluido_em = timezone.now()

            os_updated.save()

            # Dispara notificação por e-mail para o solicitante sobre a mudança
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