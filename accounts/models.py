from django.db import models
from django.contrib.auth.models import AbstractUser

class RegiaoFiscal(models.Model):
    codigo = models.IntegerField(unique=True, verbose_name="Código da Região (Ex: 10)")
    nome = models.CharField(max_length=100, verbose_name="Nome da Região Fiscal (Ex: 10ª RF - Rio Grande do Sul)")
    uf = models.CharField(max_length=50, verbose_name="Estados Jurisdicionados")

    class Meta:
        verbose_name = "Região Fiscal"
        verbose_name_plural = "Regiões Fiscais"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo}ª RF - {self.nome}"


class Unidade(models.Model):
    class TipoUnidade(models.TextChoices):
        SUPERINTENDENCIA = 'SRRF', 'Superintendência Regional'
        DELEGACIA = 'DRF', 'Delegacia da Receita Federal'
        INSPETORIA = 'IRF', 'Inspetoria da Receita Federal'
        ALFANDEGA = 'ALF', 'Alfândega'
        CUF = 'CUF', 'Centro Unificado de Fronteira'
        AGENCIA = 'ARFB', 'Agência da Receita Federal'

    regiao_fiscal = models.ForeignKey(
        RegiaoFiscal, 
        on_delete=models.CASCADE, 
        related_name='unidades',
        verbose_name="Região Fiscal"
    )
    tipo = models.CharField(max_length=10, choices=TipoUnidade.choices, default=TipoUnidade.INSPETORIA)
    nome = models.CharField(max_length=150, verbose_name="Nome da Unidade (Ex: Inspetoria de São Borja)")
    sigla = models.CharField(max_length=20, verbose_name="Sigla (Ex: IRF-SB)")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    endereco = models.CharField(max_length=200, blank=True, null=True, verbose_name="Endereço Completo")

    class Meta:
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"
        ordering = ['cidade', 'nome']

    def __str__(self):
        return f"{self.sigla} - {self.nome} ({self.cidade})"


class Usuario(AbstractUser):
    class PerfilChoices(models.TextChoices):
        SOLICITANTE = 'SOLICITANTE', 'Solicitante (Unidade)'
        GESTOR = 'GESTOR', 'Gestor Regional'

    regiao_fiscal = models.ForeignKey(
        RegiaoFiscal, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Região Fiscal"
    )
    
    # Unidade principal onde ele trabalha
    unidade = models.ForeignKey(
        Unidade, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Unidade de Lotação Principal"
    )

    # SE FOR GESTOR: Quais unidades da região estão sob a responsabilidade dele?
    unidades_gerenciadas = models.ManyToManyField(
        Unidade,
        blank=True,
        related_name='gestores',
        verbose_name="Unidades sob Gestão/Fiscalização"
    )

    telefone_whatsapp = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Celular / WhatsApp"
    )
    
    perfil = models.CharField(
        max_length=20, 
        choices=PerfilChoices.choices, 
        default=PerfilChoices.SOLICITANTE,
        verbose_name="Perfil de Acesso"
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        nome = self.get_full_name() or self.username
        if self.unidade:
            return f"{nome} - {self.unidade.sigla} ({self.unidade.cidade})"
        return nome