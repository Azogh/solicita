from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Unidade, RegiaoFiscal

@admin.register(RegiaoFiscal)
class RegiaoFiscalAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'uf')

@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'nome', 'tipo', 'cidade', 'regiao_fiscal')
    list_filter = ('regiao_fiscal', 'tipo', 'cidade')
    search_fields = ('nome', 'sigla', 'cidade')

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informações de Lotação (Solicita)', {'fields': ('regiao_fiscal', 'unidade', 'telefone_whatsapp', 'perfil')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações de Lotação (Solicita)', {'fields': ('regiao_fiscal', 'unidade', 'telefone_whatsapp', 'perfil')}),
    )
    list_display = ('username', 'first_name', 'last_name', 'regiao_fiscal', 'unidade', 'perfil', 'is_staff')
    list_filter = ('regiao_fiscal', 'perfil', 'unidade')