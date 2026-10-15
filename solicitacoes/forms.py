from django import forms
from .models import OrdemServico, FeedbackDMR, RelatorioDMRMensal


class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ['assunto', 'prioridade', 'descricao', 'os_vinculada', 'anexo_solicitante']
        widgets = {
            'assunto': forms.TextInput(attrs={'placeholder': 'Ex: Manutenção no Ar-Condicionado da Sala 102'}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descreva detalhadamente o problema ou a necessidade de serviço...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.unidade:
            self.fields['os_vinculada'].queryset = OrdemServico.objects.filter(
                unidade=user.unidade
            ).exclude(status=OrdemServico.StatusChoices.RASCUNHO)
            self.fields['os_vinculada'].empty_label = "Nenhuma (Nova Demanda Indefinida)"


class GestorAnaliseForm(forms.ModelForm):
    data_prevista_atendimento = forms.DateField(
        label="Data Prevista para Atendimento / Visita",
        required=False,
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={
                'type': 'date',
                'class': 'form-control',
            }
        )
    )

    class Meta:
        model = OrdemServico
        fields = [
            'status', 
            'data_prevista_atendimento', 
            'tecnicos_escalados', 
            'materiais_utilizados', 
            'parecer_gestor', 
            'justificativa_auditoria', 
            'justificativa_detalhes'
        ]
        widgets = {
            'tecnicos_escalados': forms.TextInput(attrs={'placeholder': 'Ex: Cristian'}),
            'materiais_utilizados': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descreva os materiais, lâmpadas, peças ou insumos aplicados no atendimento...'}),
            'parecer_gestor': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Digite as orientações técnicas para a equipe de campo ou ao solicitante...'}),
            'justificativa_detalhes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Descreva o motivo caso a demanda não possa ser atendida na data prevista...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.data_prevista_atendimento:
            self.initial['data_prevista_atendimento'] = self.instance.data_prevista_atendimento.strftime('%Y-%m-%d')


class FeedbackDMRForm(forms.ModelForm):
    class Meta:
        model = FeedbackDMR
        fields = ['ordem_servico', 'tipo', 'mensagem', 'anexo_foto']
        widgets = {
            'ordem_servico': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'mensagem': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descreva detalhadamente o feedback, elogio ou irregularidade constatada...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.unidade:
            self.fields['ordem_servico'].queryset = OrdemServico.objects.filter(
                unidade=user.unidade
            ).exclude(status=OrdemServico.StatusChoices.RASCUNHO)
            self.fields['ordem_servico'].empty_label = "Selecione uma OS (ou deixe em branco para comentário geral)"
            self.fields['ordem_servico'].required = False


class RelatorioDMRMensalForm(forms.ModelForm):
    data_visita = forms.DateField(
        label="Data da Visita Técnica no Mês",
        required=False,
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.TextInput(
            attrs={
                'class': 'form-control date-mask',
                'placeholder': 'dd/mm/aaaa',
                'autocomplete': 'off'
            }
        )
    )

    class Meta:
        model = RelatorioDMRMensal
        fields = [
            'houve_visita',
            'data_visita',
            'funcionarios_escalados',
            'prazo_cronograma_cumprido',
            'plano_manutencao_realizado',
            'servicos_eventuais_prontos',
            'equipamento_fora_uso',
            'equipamento_especificacao',
            'materiais_utilizados_observacoes',
            'outras_observacoes'
        ]
        widgets = {
            'funcionarios_escalados': forms.TextInput(attrs={'placeholder': 'Ex: Miquéias e Marcelo'}),
            'prazo_cronograma_cumprido': forms.Select(attrs={'class': 'form-select'}),
            'plano_manutencao_realizado': forms.Select(attrs={'class': 'form-select'}),
            'servicos_eventuais_prontos': forms.Select(attrs={'class': 'form-select'}),
            'equipamento_fora_uso': forms.Select(attrs={'class': 'form-select'}),
            'equipamento_especificacao': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Caso exista equipamento fora de uso, especifique qual e o motivo...'}),
            'materiais_utilizados_observacoes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Resumo dos materiais utilizados no serviço conforme repassado pela empresa...'}),
            'outras_observacoes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Pendências de serviços não realizados, dúvidas de trocas de peças, qualidade do serviço, etc.'}),
        }