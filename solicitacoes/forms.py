from django import forms
from .models import OrdemServico

class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ['assunto', 'prioridade', 'descricao', 'os_vinculada']
        widgets = {
            'assunto': forms.TextInput(attrs={'placeholder': 'Ex: Manutenção no Ar-Condicionado da Sala 102'}),
            'descricao': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Descreva detalhadamente o problema ou a necessidade de serviço...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtra as OSs vinculáveis apenas para a unidade do próprio solicitante
        if user and user.unidade:
            self.fields['os_vinculada'].queryset = OrdemServico.objects.filter(
                unidade=user.unidade
            ).exclude(status=OrdemServico.StatusChoices.RASCUNHO)
            self.fields['os_vinculada'].empty_label = "Nenhuma (Nova Demanda Indefinida)"
            self.fields['os_vinculada'].label = "Vincular a uma OS Anterior (Opcional)"