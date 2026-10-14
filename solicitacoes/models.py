from django.db import models
from django.conf import settings
from accounts.models import Unidade

class OrdemServico(models.Model):
    class StatusChoices(models.TextChoices):
        RASCUNHO = 'RASCUNHO', 'Rascunho (Não Enviado)'
        ENVIADO = 'ENVIADO', 'Solicitado (Na Caixa do Gestor)'
        EM_ATENDIMENTO = 'EM_ATENDIMENTO', 'Em Atendimento / Agendado'
        CONCLUIDO = 'CONCLUIDO', 'Concluído'
        BAIXADO = 'BAIXADO', 'Recusado / Baixado'

    class PrioridadeChoices(models.TextChoices):
        BAIXA = 'BAIXA', 'Baixa'
        MEDIA = 'MEDIA', 'Média'
        ALTA = 'ALTA', 'Alta / Urgente'

    numero_os = models.CharField(max_length=20, unique=True, editable=False, verbose_name="Número da OS")
    solicitante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='os_solicitadas', verbose_name="Solicitante")
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='ordens_servico', verbose_name="Unidade")
    
    assunto = models.CharField(max_length=200, verbose_name="Assunto / Título")
    descricao = models.TextField(verbose_name="Descrição Detalhada da Demanda")
    prioridade = models.CharField(max_length=10, choices=PrioridadeChoices.choices, default=PrioridadeChoices.MEDIA)
    
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.RASCUNHO)
    os_vinculada = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reaberturas', verbose_name="Vincular a OS Anterior")
    
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    enviado_em = models.DateTimeField(null=True, blank=True, verbose_name="Data de Envio")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Ordem de Serviço"
        verbose_name_plural = "Ordens de Serviço"
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.numero_os} - {self.assunto} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.numero_os:
            ultimo_id = OrdemServico.objects.count() + 1
            self.numero_os = f"OS-2026-{ultimo_id:04d}"
        super().save(*args, **kwargs)

    @property
    def cor_badge_status(self):
        mapa = {
            self.StatusChoices.RASCUNHO: 'danger',          # Vermelho Vivo
            self.StatusChoices.ENVIADO: 'warning text-dark', # Amarelo/Âmbar
            self.StatusChoices.EM_ATENDIMENTO: 'info',       # Laranja/Azul Atendimento
            self.StatusChoices.CONCLUIDO: 'success',         # Verde
            self.StatusChoices.BAIXADO: 'dark',              # Roxo/Escuro
        }
        return mapa.get(self.status, 'secondary')