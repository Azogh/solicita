from django.core.management.base import BaseCommand
from accounts.models import Usuario, RegiaoFiscal, Unidade

class Command(BaseCommand):
    help = 'Popula o banco de dados inicial e cria o Superusuario de desenvolvimento'

    def handle(self, *args, **kwargs):
        self.stdout.write("Configurando ambiente de desenvolvimento...")

        # 1. Garante a Região Fiscal
        rf10, _ = RegiaoFiscal.objects.get_or_create(
            codigo=10,
            defaults={'nome': '10ª RF - 10ª Região Fiscal - RS'}
        )

        # 2. Garante a Unidade Principal
        unidade_sb, _ = Unidade.objects.get_or_create(
            sigla='IRF/SBJ',
            defaults={
                'nome': 'Inspetoria da Receita Federal em São Borja',
                'cidade': 'São Borja',
                'regiao_fiscal': rf10
            }
        )

        # 3. Cria/Atualiza o Superusuário Admin
        admin_email = 'admin@rfb.gov.br'
        admin_user, created = Usuario.objects.get_or_create(
            email=admin_email,
            defaults={
                'username': admin_email,
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'perfil': Usuario.PerfilChoices.GESTOR,
                'regiao_fiscal': rf10,
                'unidade': unidade_sb,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )

        admin_user.set_password('admin')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Superusuario '{admin_email}' criado com sucesso! (Senha: admin)"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Senha do Superusuario '{admin_email}' redefinida para 'admin'!"))