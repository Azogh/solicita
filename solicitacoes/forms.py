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
    class Meta:
        model = OrdemServico
        fields = ['status', 'data_prevista_atendimento', 'parecer_gestor', 'justificativa_auditoria', 'justificativa_detalhes']
        widgets = {
            'data_prevista_atendimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'parecer_gestor': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Digite as orientações técnicas para a equipe de campo ou ao solicitante...'}),
            'justificativa_detalhes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Descreva o motivo caso a demanda não possa ser atendida na data prevista...'}),
        }


class FeedbackDMRForm(forms.ModelForm):
    class Meta:
        model = FeedbackDMR
        fields = ['tipo', 'mensagem', 'anexo_foto']
        widgets = {
            'mensagem': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descreva detalhadamente o feedback, elogio ou irregularidade constatada na prestação do serviço...'}),
        }