from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Unidade

class SolicitanteCadastroForm(UserCreationForm):
    first_name = forms.CharField(label="Nome", max_length=30, required=True)
    last_name = forms.CharField(label="Sobrenome", max_length=150, required=True)
    email = forms.EmailField(label="E-mail Institucional", required=True)
    unidade = forms.ModelChoiceField(
        queryset=Unidade.objects.all(),
        label="Sua Unidade",
        empty_label="Selecione a sua unidade...",
        required=True
    )
    telefone_whatsapp = forms.CharField(
        label="Celular / WhatsApp",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '(00) 90000-0000'})
    )

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('first_name', 'last_name', 'email', 'unidade', 'telefone_whatsapp')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Usa o e-mail como username de login
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.unidade = self.cleaned_data['unidade']
        user.telefone_whatsapp = self.cleaned_data['telefone_whatsapp']
        user.perfil = Usuario.PerfilChoices.SOLICITANTE
        if commit:
            user.save()
        return user