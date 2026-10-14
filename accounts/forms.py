from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Unidade, RegiaoFiscal

class SolicitanteCadastroForm(UserCreationForm):
    first_name = forms.CharField(label="Nome", max_length=30, required=True)
    last_name = forms.CharField(label="Sobrenome", max_length=150, required=True)
    email = forms.EmailField(label="E-mail Institucional", required=True)
    
    perfil = forms.ChoiceField(
        choices=Usuario.PerfilChoices.choices,
        label="Perfil de Acesso",
        initial=Usuario.PerfilChoices.SOLICITANTE,
        widget=forms.RadioSelect(attrs={'class': 'btn-check-perfil'})
    )

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
        queryset=Unidade.objects.none(),
        label="Sua Unidade / Repartição Principal",
        empty_label="Primeiro selecione a Região Fiscal...",
        required=True
    )

    unidades_gerenciadas = forms.ModelMultipleChoiceField(
        queryset=Unidade.objects.all(),
        label="Unidades sob sua Jurisdição/Fiscalização",
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    telefone_whatsapp = forms.CharField(
        label="Celular / WhatsApp",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '(55) 90000-0000'})
    )

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('first_name', 'last_name', 'email', 'perfil', 'regiao_fiscal', 'unidade', 'unidades_gerenciadas', 'telefone_whatsapp')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'regiao_fiscal' in self.data:
            try:
                regiao_id = int(self.data.get('regiao_fiscal'))
                unidades_qs = Unidade.objects.filter(regiao_fiscal_id=regiao_id)
                self.fields['unidade'].queryset = unidades_qs
                self.fields['unidades_gerenciadas'].queryset = unidades_qs
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.regiao_fiscal:
            unidades_qs = self.instance.regiao_fiscal.unidades.all()
            self.fields['unidade'].queryset = unidades_qs
            self.fields['unidades_gerenciadas'].queryset = unidades_qs

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.perfil = self.cleaned_data['perfil']
        user.regiao_fiscal = self.cleaned_data['regiao_fiscal']
        user.unidade = self.cleaned_data['unidade']
        user.telefone_whatsapp = self.cleaned_data['telefone_whatsapp']

        if user.perfil == Usuario.PerfilChoices.GESTOR:
            user.is_active = False

        if commit:
            user.save()
            self.save_m2m()
            if user.perfil == Usuario.PerfilChoices.GESTOR:
                user.unidades_gerenciadas.set(self.cleaned_data['unidades_gerenciadas'])
        return user


class PerfilEditarForm(forms.ModelForm):
    first_name = forms.CharField(label="Nome", required=False, widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext fw-bold'}))
    last_name = forms.CharField(label="Sobrenome", required=False, widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext fw-bold'}))
    email = forms.EmailField(label="E-mail Institucional", required=False, widget=forms.EmailInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext fw-bold'}))
    telefone_whatsapp = forms.CharField(label="Celular / WhatsApp", max_length=20, required=False)

    class Meta:
        model = Usuario
        fields = ('first_name', 'last_name', 'email', 'telefone_whatsapp')

    def clean_first_name(self):
        return self.instance.first_name  # Garante que o valor no banco não muda no POST

    def clean_last_name(self):
        return self.instance.last_name

    def clean_email(self):
        return self.instance.email