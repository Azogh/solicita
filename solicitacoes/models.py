from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import Unidade, Usuario


class OrdemServico(models.Model):
    class StatusChoices(models.TextChoices):
        RASCUNHO = 'RASCUNHO', 'Rascunho'
        ENVIADO = 'ENVIADO', 'Enviado (Aguardando Análise)'
        EM_ATENDIMENTO = 'EM_ATENDIMENTO', 'Em Atendimento / Agendado'
        CONCLUIDO = 'CONCLUIDO', 'Concluído'
        CANCELADO = 'CANCELADO', 'Cancelado'

    class PrioridadeChoices(models.TextChoices):
        BAIXA = 'BAIXA', 'Prioridade Baixa'
        NORMAL = 'NORMAL', 'Normal'
        URGENTE = 'URGENTE', 'Urgente'
        URGENTISSIMO = 'URGENTISSIMO', 'Urgentíssimo'

    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='ordens_servico')
    solicitante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='minhas_os')
    numero_os = models.CharField(max_length=30, unique=True, editable=False)
    assunto = models.CharField(max_length=150)
    prioridade = models.CharField(max_length=20, choices=PrioridadeChoices.choices, default=PrioridadeChoices.NORMAL)
    descricao = models.TextField(verbose_name="Descrição Sucinta do Problema")
    
    # Anexo e Histórico
    anexo_solicitante = models.FileField(upload_to='anexos_os/', null=True, blank=True)
    os_vinculada = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reiteracoes')
    
    # Análise do Gestor & Execução
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.RASCUNHO)
    data_prevista_atendimento = models.DateField(null=True, blank=True)
    tecnicos_escalados = models.CharField(max_length=200, default='Cristian', null=True, blank=True, verbose_name="Responsável / Fiscal Preposto")
    materiais_utilizados = models.TextField(null=True, blank=True, verbose_name="Materiais e Peças Utilizadas")
    parecer_gestor = models.TextField(null=True, blank=True)
    
    # Auditoria e Impedimentos
    justificativa_auditoria = models.CharField(max_length=100, null=True, blank=True)
    justificativa_detalhes = models.TextField(null=True, blank=True)

    # Datas de Controle
    criado_em = models.DateTimeField(auto_now_add=True)
    enviado_em = models.DateTimeField(null=True, blank=True)
    agendado_em = models.DateTimeField(null=True, blank=True)
    concluido_em = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.numero_os or "ExtractYear" in self.numero_os:
            ano = timezone.now().year
            ultimo_id = OrdemServico.objects.count() + 1
            self.numero_os = f"OS-{ano}-{ultimo_id:04d}"
        super().save(*args, **kwargs)

    @property
    def cor_badge_status(self):
        mapa = {
            self.StatusChoices.RASCUNHO: 'secondary',
            self.StatusChoices.ENVIADO: 'warning text-dark',
            self.StatusChoices.EM_ATENDIMENTO: 'info text-dark',
            self.StatusChoices.CONCLUIDO: 'success',
            self.StatusChoices.CANCELADO: 'danger',
        }
        return mapa.get(self.status, 'secondary')

    @property
    def cor_badge_prioridade(self):
        mapa = {
            self.PrioridadeChoices.BAIXA: 'secondary',
            self.PrioridadeChoices.NORMAL: 'primary',
            self.PrioridadeChoices.URGENTE: 'danger',
            self.PrioridadeChoices.URGENTISSIMO: 'danger fw-bold',
        }
        return mapa.get(self.prioridade, 'secondary')

    def __str__(self):
        return f"{self.numero_os} - {self.assunto} ({self.unidade.sigla})"


class FeedbackDMR(models.Model):
    class TipoChoices(models.TextChoices):
        ELOGIO = 'ELOGIO', 'Elogio'
        OBSERVACAO = 'OBSERVACAO', 'Observação / Apontamento'
        RECLAMACAO = 'RECLAMACAO', 'Reclamação / Irregularidade'

    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='feedbacks_dmr')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')
    tipo = models.CharField(max_length=20, choices=TipoChoices.choices, default=TipoChoices.OBSERVACAO)
    mensagem = models.TextField()
    anexo_foto = models.FileField(upload_to='feedbacks_dmr/', null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.unidade.sigla} ({self.criado_em.strftime('%d/%m/%Y')})"


class RelatorioDMRMensal(models.Model):
    class SimNaoChoices(models.TextChoices):
        SIM = 'SIM', 'Sim'
        NAO = 'NAO', 'Não'

    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='relatorios_dmr_mensais')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mes_referencia = models.IntegerField(verbose_name="Mês (1-12)")
    ano_referencia = models.IntegerField(verbose_name="Ano")
    data_visita = models.DateField(null=True, blank=True)
    houve_visita = models.BooleanField(default=True, verbose_name="Houve visita técnica no mês?")
    
    funcionarios_escalados = models.CharField(max_length=255, default='Cristian', null=True, blank=True, verbose_name="1- Responsável / Fiscal Preposto pelo Serviço")
    prazo_cronograma_cumprido = models.CharField(max_length=3, choices=SimNaoChoices.choices, default=SimNaoChoices.SIM, verbose_name="2- Manutenção executada no prazo?")
    plano_manutencao_realizado = models.CharField(max_length=3, choices=SimNaoChoices.choices, default=SimNaoChoices.SIM, verbose_name="3- Serviços do plano todos realizados?")
    servicos_eventuais_prontos = models.CharField(max_length=3, choices=SimNaoChoices.choices, default=SimNaoChoices.SIM, verbose_name="4- Serviços eventuais prontamente realizados?")
    equipamento_fora_uso = models.CharField(max_length=3, choices=SimNaoChoices.choices, default=SimNaoChoices.NAO, verbose_name="5- Existe equipamento fora de uso por falta de manutenção?")
    equipamento_especificacao = models.TextField(null=True, blank=True, verbose_name="Especificar equipamento fora de uso")
    materiais_utilizados_observacoes = models.TextField(null=True, blank=True, verbose_name="6- Materiais e quantidades informadas")
    outras_observacoes = models.TextField(null=True, blank=True, verbose_name="7- Outras observações (Pendências, Qualidade)")

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('unidade', 'mes_referencia', 'ano_referencia')

    def __str__(self):
        return f"DMR {self.mes_referencia:02d}/{self.ano_referencia} - {self.unidade.sigla}"