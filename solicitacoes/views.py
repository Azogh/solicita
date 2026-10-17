from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import OrdemServico, FeedbackDMR, RelatorioDMRMensal
from .forms import OrdemServicoForm, GestorAnaliseForm, FeedbackDMRForm, RelatorioDMRMensalForm
from accounts.models import Usuario
from .utils import render_to_pdf


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
                        f"• Data Prevista de Atendimento: {os_updated.data_prevista_atendimento.strftime('%d/%m/%Y') if os_updated.data_prevista_atendimento else 'Não informada'}\n"
                        f"• Responsável/Preposto: {os_updated.tecnicos_escalados or 'Cristian'}\n\n"
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
        tecnicos = request.POST.get('tecnicos_escalados', 'Cristian')
        
        if os_id and data_agendada_raw:
            try:
                if '/' in data_agendada_raw:
                    dia, mes, ano = data_agendada_raw.split('/')
                    data_agendada = f"{ano}-{mes}-{dia}"
                else:
                    data_agendada = data_agendada_raw

                os_target = get_object_or_404(OrdemServico, pk=os_id, unidade_id__in=unidades_ids)
                os_target.data_prevista_atendimento = data_agendada
                os_target.tecnicos_escalados = tecnicos or 'Cristian'
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
    
    peso_prioridade = {'URGENTISSIMO': 4, 'URGENTE': 3, 'NORMAL': 2, 'BAIXA': 1}
    mapa_prioridade_display = {'URGENTISSIMO': 'Urgentíssimo', 'URGENTE': 'Urgente', 'NORMAL': 'Normal', 'BAIXA': 'Baixa'}

    for i in range(14):
        dia_corrente = hoje + timedelta(days=i)
        if dia_corrente.weekday() < 5:
            os_no_dia = os_agendadas.filter(data_prevista_atendimento=dia_corrente)
            
            prioridade_mais_alta = "Nenhuma"
            maior_peso = 0
            for item in os_no_dia:
                peso = peso_prioridade.get(item.prioridade, 0)
                if peso > maior_peso:
                    maior_peso = peso
                    prioridade_mais_alta = mapa_prioridade_display.get(item.prioridade, 'Normal')

            dias_grade.append({
                'data': dia_corrente,
                'dia_semana': dia_corrente.strftime('%A'),
                'os_list': os_no_dia,
                'total_os': os_no_dia.count(),
                'prioridade_maxima': prioridade_mais_alta
            })

    tem_urgente_pendente = os_pendentes.filter(prioridade__in=['URGENTE', 'URGENTISSIMO']).exists()

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
            
            messages.success(request, "Feedback registrado com sucesso!")
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
    feedbacks = FeedbackDMR.objects.filter(unidade_id__in=unidades_ids).order_by('-criado_em')

    return render(request, 'solicitacoes/listar_feedbacks_dmr.html', {
        'feedbacks': feedbacks
    })


@login_required
def criar_relatorio_dmr_mensal_view(request):
    user = request.user
    if not user.unidade:
        messages.error(request, "Usuário não possui unidade vinculada para emissão do DMR.")
        return redirect('dashboard')

    hoje = date.today()
    mes_ref = hoje.month
    ano_ref = hoje.year

    os_do_mes = OrdemServico.objects.filter(
        unidade=user.unidade,
        data_prevista_atendimento__month=mes_ref,
        data_prevista_atendimento__year=ano_ref
    )
    
    tecnicos_auto = ", ".join(filter(None, set(os_do_mes.values_list('tecnicos_escalados', flat=True))))
    materiais_auto = "\n".join(filter(None, set(os_do_mes.values_list('materiais_utilizados', flat=True))))

    relatorio_existente = RelatorioDMRMensal.objects.filter(
        unidade=user.unidade, mes_referencia=mes_ref, ano_referencia=ano_ref
    ).first()

    if request.method == 'POST':
        form = RelatorioDMRMensalForm(request.POST, instance=relatorio_existente)
        if form.is_valid():
            relatorio = form.save(commit=False)
            relatorio.unidade = user.unidade
            relatorio.autor = user
            relatorio.mes_referencia = mes_ref
            relatorio.ano_referencia = ano_ref
            relatorio.save()

            messages.success(request, f"Relatório DMR Mensal de {mes_ref:02d}/{ano_ref} salvo com sucesso!")
            return redirect('dashboard')
    else:
        initial_data = {
            'funcionarios_escalados': tecnicos_auto or "Cristian",
            'materiais_utilizados_observacoes': materiais_auto or "",
        }
        form = RelatorioDMRMensalForm(instance=relatorio_existente, initial=initial_data)

    return render(request, 'solicitacoes/criar_relatorio_dmr_mensal.html', {
        'form': form,
        'mes_ref': mes_ref,
        'ano_ref': ano_ref,
        'relatorio_existente': relatorio_existente
    })


@login_required
def central_relatorios_dmr_view(request):
    user = request.user
    if user.perfil != Usuario.PerfilChoices.GESTOR:
        messages.error(request, "Acesso restrito a gestores.")
        return redirect('dashboard')

    hoje = date.today()
    mes_filtro = int(request.GET.get('mes', hoje.month))
    ano_filtro = int(request.GET.get('ano', hoje.year))

    unidades_jurisdicao = user.unidades_gerenciadas.all()
    unidades_ids = unidades_jurisdicao.values_list('id', flat=True)

    relatorios = RelatorioDMRMensal.objects.filter(
        unidade_id__in=unidades_ids,
        mes_referencia=mes_filtro,
        ano_referencia=ano_filtro
    ).select_related('unidade', 'autor')

    unidades_emitidas_ids = relatorios.values_list('unidade_id', flat=True)
    unidades_pendentes = unidades_jurisdicao.exclude(id__in=unidades_emitidas_ids)

    context = {
        'relatorios': relatorios,
        'unidades_pendentes': unidades_pendentes,
        'mes_filtro': mes_filtro,
        'ano_filtro': ano_filtro,
        'total_jurisdicao': unidades_jurisdicao.count(),
        'total_emitidos': relatorios.count(),
        'total_pendentes_count': unidades_pendentes.count(),
    }
    return render(request, 'solicitacoes/central_relatorios_dmr.html', context)


@login_required
def detalhar_relatorio_dmr_view(request, pk):
    relatorio = get_object_or_404(RelatorioDMRMensal, pk=pk)
    return render(request, 'solicitacoes/detalhar_relatorio_dmr.html', {'relatorio': relatorio})


@login_required
def exportar_dmr_pdf_view(request, pk):
    """ Gera e faz o download do PDF individual do DMR """
    relatorio = get_object_or_404(RelatorioDMRMensal, pk=pk)
    
    context = {
        'relatorio': relatorio,
        'user': request.user,
    }
    
    pdf = render_to_pdf('solicitacoes/pdf/dmr_pdf_template.html', context)
    if pdf:
        response = pdf
        filename = f"DMR_{relatorio.unidade.sigla}_{relatorio.mes_referencia:02d}_{relatorio.ano_referencia}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    messages.error(request, "Erro ao gerar arquivo PDF do DMR.")
    return redirect('detalhar_relatorio_dmr', pk=pk)


@login_required
def exportar_grade_semanal_pdf_view(request):
    """ Gera e faz o download do PDF da Grade Semanal do Gestor """
    user = request.user
    if user.perfil != Usuario.PerfilChoices.GESTOR:
        messages.error(request, "Acesso restrito a gestores.")
        return redirect('dashboard')

    unidades_ids = user.unidades_gerenciadas.values_list('id', flat=True)
    os_agendadas = OrdemServico.objects.filter(
        unidade_id__in=unidades_ids,
        status=OrdemServico.StatusChoices.EM_ATENDIMENTO,
        data_prevista_atendimento__isnull=False
    ).order_by('data_prevista_atendimento')

    hoje = date.today()
    dias_grade = []
    
    peso_prioridade = {'URGENTISSIMO': 4, 'URGENTE': 3, 'NORMAL': 2, 'BAIXA': 1}
    mapa_prioridade_display = {'URGENTISSIMO': 'Urgentíssimo', 'URGENTE': 'Urgente', 'NORMAL': 'Normal', 'BAIXA': 'Baixa'}

    for i in range(14):
        dia_corrente = hoje + timedelta(days=i)
        if dia_corrente.weekday() < 5:
            os_no_dia = os_agendadas.filter(data_prevista_atendimento=dia_corrente)
            
            prioridade_mais_alta = "Nenhuma"
            maior_peso = 0
            for item in os_no_dia:
                peso = peso_prioridade.get(item.prioridade, 0)
                if peso > maior_peso:
                    maior_peso = peso
                    prioridade_mais_alta = mapa_prioridade_display.get(item.prioridade, 'Normal')

            dias_grade.append({
                'data': dia_corrente,
                'dia_semana': dia_corrente.strftime('%A'),
                'os_list': os_no_dia,
                'total_os': os_no_dia.count(),
                'prioridade_maxima': prioridade_mais_alta
            })

    context = {
        'dias_grade': dias_grade,
        'user': request.user,
        'hoje': hoje,
    }

    pdf = render_to_pdf('solicitacoes/pdf/grade_semanal_pdf_template.html', context)
    if pdf:
        response = pdf
        filename = f"Grade_Semanal_{hoje.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    messages.error(request, "Erro ao gerar arquivo PDF da Grade Semanal.")
    return redirect('cronograma_visitas')


@login_required
def exportar_dmrs_selecionados_pdf_view(request):
    """ Exporta múltiplos DMRs selecionados via checkbox num único PDF (1 por página) """
    if request.method == 'POST':
        ids_selecionados = request.POST.getlist('relatorios_ids')
        if not ids_selecionados:
            messages.warning(request, "Selecione ao menos um relatório DMR para baixar.")
            return redirect('central_relatorios_dmr')

        relatorios = RelatorioDMRMensal.objects.filter(
            id__in=ids_selecionados,
            unidade__in=request.user.unidades_gerenciadas.all()
        ).select_related('unidade', 'autor')

        context = {
            'relatorios': relatorios,
            'user': request.user,
        }

        pdf = render_to_pdf('solicitacoes/pdf/dmr_lote_pdf_template.html', context)
        if pdf:
            response = pdf
            response['Content-Disposition'] = 'attachment; filename="DMRs_Compilados_Jurisdicao.pdf"'
            return response

    messages.error(request, "Erro ao gerar arquivo compilado de DMRs.")
    return redirect('central_relatorios_dmr')


@login_required
def exportar_imr_consolidado_jurisdicao_pdf_view(request):
    """ Gera o Relatório Executivo/Sintético do IMR da Jurisdição do Gestor """
    user = request.user
    if user.perfil != Usuario.PerfilChoices.GESTOR:
        messages.error(request, "Acesso restrito a gestores.")
        return redirect('dashboard')

    hoje = date.today()
    mes_filtro = int(request.GET.get('mes', hoje.month))
    ano_filtro = int(request.GET.get('ano', hoje.year))

    unidades_jurisdicao = user.unidades_gerenciadas.all()
    unidades_ids = unidades_jurisdicao.values_list('id', flat=True)

    relatorios = RelatorioDMRMensal.objects.filter(
        unidade_id__in=unidades_ids,
        mes_referencia=mes_filtro,
        ano_referencia=ano_filtro
    ).select_related('unidade')

    total_unidades = unidades_jurisdicao.count()
    total_emitidos = relatorios.count()
    unidades_com_visita = relatorios.filter(houve_visita=True).count()
    
    total_os_mes = OrdemServico.objects.filter(
        unidade_id__in=unidades_ids,
        data_prevista_atendimento__month=mes_filtro,
        data_prevista_atendimento__year=ano_filtro
    )
    
    os_concluidas = total_os_mes.filter(status=OrdemServico.StatusChoices.CONCLUIDO).count()
    feedbacks_mes = FeedbackDMR.objects.filter(
        unidade_id__in=unidades_ids,
        criado_em__month=mes_filtro,
        criado_em__year=ano_filtro
    )

    unidades_emitidas_ids = relatorios.values_list('unidade_id', flat=True)
    unidades_pendentes = unidades_jurisdicao.exclude(id__in=unidades_emitidas_ids)

    context = {
        'mes_filtro': mes_filtro,
        'ano_filtro': ano_filtro,
        'relatorios': relatorios,
        'unidades_pendentes': unidades_pendentes,
        'total_unidades': total_unidades,
        'total_emitidos': total_emitidos,
        'unidades_com_visita': unidades_com_visita,
        'total_os_count': total_os_mes.count(),
        'os_concluidas': os_concluidas,
        'feedbacks_count': feedbacks_mes.count(),
        'user': user,
        'hoje': hoje,
    }

    pdf = render_to_pdf('solicitacoes/pdf/imr_consolidado_pdf_template.html', context)
    if pdf:
        response = pdf
        filename = f"IMR_Consolidado_Jurisdicao_{mes_filtro:02d}_{ano_filtro}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    messages.error(request, "Erro ao gerar o IMR Consolidado.")
    return redirect('central_relatorios_dmr')