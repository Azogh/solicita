from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Unidade, RegiaoFiscal

class SolicitanteCadastroForm(UserCreationForm):
    first_name = forms.CharField(label="Nome", max_length=30, required=True)
    last_name = forms.CharField(label="Sobrenome", max_length=150, required=True)
    email = forms.EmailField(label="E-mail Institucional", required=True)
    
    regiao_fiscal = forms.ModelChoiceField(
        queryset=RegiaoFiscal.objects.all(),
        label="Região Fiscal",
        empty_label="Selecione a Região Fiscal...",
        required=True,
        widget=forms.Select(attrs={
            'hx-get': '/accounts/buscar-unidades/',
            'hx-target': '#id_unidade',
            'hx-trigger': 'change'
        })
    )
    
    unidade = forms.ModelChoiceField(
        queryset=Unidade.objects.none(),  # Inicia vazio até selecionar a Região Fiscal
        label="Sua Unidade / Repartição",
        empty_label="Primeiro selecione a Região Fiscal...",
        required=True
    )
    
    telefone_whatsapp = forms.CharField(
        label="Celular / WhatsApp",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '(55) 90000-0000'})
    )

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('first_name', 'last_name', 'email', 'regiao_fiscal', 'unidade', 'telefone_whatsapp')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se houver dados submetidos no POST ou formulário vinculado, popula as unidades válidas
        if 'regiao_fiscal' in self.data:
            try:
                regiao_id = int(self.data.get('regiao_fiscal'))
                self.fields['unidade'].queryset = Unidade.objects.filter(regiao_fiscal_id=regiao_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.regiao_fiscal:
            self.fields['unidade'].queryset = self.instance.regiao_fiscal.unidades.all()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.regiao_fiscal = self.cleaned_data['regiao_fiscal']
        user.unidade = self.cleaned_data['unidade']
        user.telefone_whatsapp = self.cleaned_data['telefone_whatsapp']
        user.perfil = Usuario.PerfilChoices.SOLICITANTE
        if commit:
            user.save()
        return user