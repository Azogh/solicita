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

    class JustificativaChoices(models.TextChoices):
        EFETIVO = 'EFETIVO', 'Falta de Efetivo / Mão de Obra'
        VERBA = 'VERBA', 'Falta de Verba / Contrato de Peças'
        REAGENDADO = 'REAGENDADO', 'Reagendado a Pedido da Unidade'
        CLIMA = 'CLIMA', 'Condições Climáticas / Acesso Impedido'
        OUTROS = 'OUTROS', 'Outros Motivos Operacionais'

    # Identificação
    numero_os = models.CharField(max_length=20, unique=True, editable=False, verbose_name="Número da OS")
    solicitante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='os_solicitadas', verbose_name="Solicitante")
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='ordens_servico', verbose_name="Unidade")
    
    # Conteúdo da Solicitação
    assunto = models.CharField(max_length=200, verbose_name="Assunto / Título")
    descricao = models.TextField(verbose_name="Descrição Detalhada da Demanda")
    prioridade = models.CharField(max_length=10, choices=PrioridadeChoices.choices, default=PrioridadeChoices.MEDIA)
    anexo_solicitante = models.FileField(upload_to='anexos_solicitacoes/', null=True, blank=True, verbose_name="Anexo / Foto do Solicitante")
    
    # Status e Fluxo
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.RASCUNHO)
    os_vinculada = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reaberturas', verbose_name="Vincular a OS Anterior")
    
    # Gestão, Agendamento e Parecer
    data_prevista_atendimento = models.DateField(null=True, blank=True, verbose_name="Data Prevista para Atendimento / Visita")
    parecer_gestor = models.TextField(null=True, blank=True, verbose_name="Parecer Técnico do Gestor")
    justificativa_auditoria = models.CharField(max_length=20, choices=JustificativaChoices.choices, null=True, blank=True, verbose_name="Justificativa de Auditoria / Atraso")
    justificativa_detalhes = models.TextField(null=True, blank=True, verbose_name="Detalhamento da Justificativa")
    
    # Datas de Auditoria
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    enviado_em = models.DateTimeField(null=True, blank=True, verbose_name="Data de Envio")
    agendado_em = models.DateTimeField(null=True, blank=True, verbose_name="Data do Agendamento")
    concluido_em = models.DateTimeField(null=True, blank=True, verbose_name="Data de Conclusão")
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


class FeedbackDMR(models.Model):
    class TipoChoice(models.TextChoices):
        RECLAMACAO = 'RECLAMACAO', 'Reclamação'
        ELOGIO = 'ELOGIO', 'Elogio'
        COMENTARIO = 'COMENTARIO', 'Comentário / Sugestão'

    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='feedbacks', null=True, blank=True, verbose_name="Ordem de Serviço Relacionada")
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='feedbacks_dmr', verbose_name="Unidade")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Autor")
    tipo = models.CharField(max_length=20, choices=TipoChoice.choices, default=TipoChoice.COMENTARIO)
    mensagem = models.TextField(verbose_name="Relato / Comentário")
    anexo_foto = models.FileField(upload_to='feedbacks_dmr/', null=True, blank=True, verbose_name="Anexo / Foto de Comprovação")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data do Registro")

    class Meta:
        verbose_name = "Feedback DMR/IMR"
        verbose_name_plural = "Feedbacks DMR/IMR"
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.unidade.sigla} ({self.criado_em.strftime('%d/%m/%Y')})"