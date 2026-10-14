from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import OrdemServico
from .forms import OrdemServicoForm

@login_required
def criar_os_view(request):
    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, user=request.user)
        if form.is_valid():
            os_item = form.save(commit=False)
            os_item.solicitante = request.user
            os_item.unidade = request.user.unidade
            
            # Verifica qual botão foi clicado na tela
            if 'btn_enviar' in request.POST:
                os_item.status = OrdemServico.StatusChoices.ENVIADO
                os_item.enviado_em = timezone.now()
                messages.success(request, f"Ordem de Serviço {os_item.numero_os} enviada com sucesso para a caixa do Gestor!")
            else:
                os_item.status = OrdemServico.StatusChoices.RASCUNHO
                messages.info(request, f"Rascunho da OS {os_item.numero_os} salvo. Você pode editá-la antes de enviar.")
            
            os_item.save()
            return redirect('dashboard')
    else:
        form = OrdemServicoForm(user=request.user)
    
    return render(request, 'solicitacoes/criar_os.html', {'form': form})

@login_required
def editar_os_view(request, pk):
    os_item = get_object_or_404(OrdemServico, pk=pk, solicitante=request.user)
    
    # Bloqueio de segurança: Se a OS já foi enviada, não permite mais edição
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
                messages.success(request, f"Ordem de Serviço {os_updated.numero_os} enviada com sucesso!")
            else:
                messages.info(request, "Rascunho atualizado com sucesso.")
            
            os_updated.save()
            return redirect('dashboard')
    else:
        form = OrdemServicoForm(instance=os_item, user=request.user)

    return render(request, 'solicitacoes/editar_os.html', {'form': form, 'os_item': os_item})

@login_required
def detalhar_os_view(request, pk):
    os_item = get_object_or_404(OrdemServico, pk=pk)
    return render(request, 'solicitacoes/detalhar_os.html', {'os_item': os_item})