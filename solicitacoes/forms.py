from django import forms
from .models import OrdemServico, FeedbackDMR

class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ['assunto', 'prioridade', 'descricao', 'os_vinculada', 'anexo_solicitante']
        widgets = {
            'assunto': forms.TextInput(attrs={'placeholder': 'Ex: Manutenção no Ar-Condicionado da Sala 102'}),
            'descricao': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Descreva detalhadamente o problema ou a necessidade de serviço...'}),
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
        model = OrdemServico
        fields = ['status', 'data_prevista_atendimento', 'parecer_gestor', 'justificativa_auditoria', 'justificativa_detalhes']
        widgets = {
            'parecer_gestor': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Digite as orientações técnicas para a equipe de campo ou ao solicitante...'}),
            'justificativa_detalhes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Descreva o motivo caso a demanda não possa ser atendida na data prevista...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.data_prevista_atendimento:
            self.initial['data_prevista_atendimento'] = self.instance.data_prevista_atendimento.strftime('%d/%m/%Y')

class FeedbackDMRForm(forms.ModelForm):
    class Meta:
        model = FeedbackDMR
        fields = ['ordem_servico', 'tipo', 'mensagem', 'anexo_foto']
        widgets = {
            'ordem_servico': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'mensagem': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descreva detalhadamente o feedback, elogio ou irregularidade constatada na prestação do serviço...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.unidade:
            # Lista apenas as OSs da unidade do solicitante para vinculação
            self.fields['ordem_servico'].queryset = OrdemServico.objects.filter(
                unidade=user.unidade
            ).exclude(status=OrdemServico.StatusChoices.RASCUNHO)
            self.fields['ordem_servico'].empty_label = "Selecione uma OS (ou deixe em branco para comentário geral)"
            self.fields['ordem_servico'].required = False