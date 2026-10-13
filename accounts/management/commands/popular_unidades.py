from django.core.management.base import BaseCommand
from accounts.models import RegiaoFiscal, Unidade

class Command(BaseCommand):
    help = 'Popula a 10ª Região Fiscal (RS) e suas Unidades no banco de dados'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando a carga de dados da 10ª Região Fiscal...")

        # 1. Região Fiscal (RS)
        rf10, _ = RegiaoFiscal.objects.get_or_create(
            codigo=10,
            defaults={
                'nome': '10ª Região Fiscal - Rio Grande do Sul',
                'uf': 'RS'
            }
        )

        # 2. Mapeamento de Unidades do RS
        unidades_data = [
            # Superintendência
            {"tipo": Unidade.TipoUnidade.SUPERINTENDENCIA, "sigla": "SRRF10", "nome": "Superintendência Regional da 10ª RF", "cidade": "Porto Alegre"},
            
            # Delegacias (DRF)
            {"tipo": Unidade.TipoUnidade.DELEGACIA, "sigla": "DRF/POA", "nome": "Delegacia da Receita Federal em Porto Alegre", "cidade": "Porto Alegre"},
            {"tipo": Unidade.TipoUnidade.DELEGACIA, "sigla": "DRF/CXS", "nome": "Delegacia da Receita Federal em Caxias do Sul", "cidade": "Caxias do Sul"},
            {"tipo": Unidade.TipoUnidade.DELEGACIA, "sigla": "DRF/PFN", "nome": "Delegacia da Receita Federal em Passo Fundo", "cidade": "Passo Fundo"},
            {"tipo": Unidade.TipoUnidade.DELEGACIA, "sigla": "DRF/PEL", "nome": "Delegacia da Receita Federal em Pelotas", "cidade": "Pelotas"},
            {"tipo": Unidade.TipoUnidade.DELEGACIA, "sigla": "DRF/SMA", "nome": "Delegacia da Receita Federal em Santa Maria", "cidade": "Santa Maria"},
            {"tipo": Unidade.TipoUnidade.DELEGACIA, "sigla": "DRF/SCR", "nome": "Delegacia da Receita Federal em Santa Cruz do Sul", "cidade": "Santa Cruz do Sul"},
            {"tipo": Unidade.TipoUnidade.DELEGACIA, "sigla": "DRF/STO", "nome": "Delegacia da Receita Federal em Santo Ângelo", "cidade": "Santo Ângelo"},

            # Alfândegas (ALF)
            {"tipo": Unidade.TipoUnidade.ALFANDEGA, "sigla": "ALF/URG", "nome": "Alfândega da Receita Federal em Uruguaiana", "cidade": "Uruguaiana"},
            {"tipo": Unidade.TipoUnidade.ALFANDEGA, "sigla": "ALF/SCL", "nome": "Alfândega da Receita Federal em Santana do Livramento", "cidade": "Santana do Livramento"},
            {"tipo": Unidade.TipoUnidade.ALFANDEGA, "sigla": "ALF/RGO", "nome": "Alfândega da Receita Federal em Rio Grande", "cidade": "Rio Grande"},
            {"tipo": Unidade.TipoUnidade.ALFANDEGA, "sigla": "ALF/POA", "nome": "Alfândega da Receita Federal no Aeroporto de Porto Alegre", "cidade": "Porto Alegre"},

            # Inspetorias (IRF) e Postos
            {"tipo": Unidade.TipoUnidade.INSPETORIA, "sigla": "IRF/SBJ", "nome": "Inspetoria da Receita Federal em São Borja", "cidade": "São Borja"},
            {"tipo": Unidade.TipoUnidade.CUF, "sigla": "CUF/SBJ", "nome": "Centro Unificado de Fronteira - Ponte Internacional", "cidade": "São Borja"},
            {"tipo": Unidade.TipoUnidade.INSPETORIA, "sigla": "IRF/CHU", "nome": "Inspetoria da Receita Federal no Chuí", "cidade": "Chuí"},
            {"tipo": Unidade.TipoUnidade.INSPETORIA, "sigla": "IRF/JAG", "nome": "Inspetoria da Receita Federal em Jaguarão", "cidade": "Jaguarão"},
            {"tipo": Unidade.TipoUnidade.INSPETORIA, "sigla": "IRF/IQU", "nome": "Inspetoria da Receita Federal em Itaqui", "cidade": "Itaqui"},
            {"tipo": Unidade.TipoUnidade.INSPETORIA, "sigla": "IRF/PSL", "nome": "Inspetoria da Receita Federal em Porto Xavier", "cidade": "Porto Xavier"},
            {"tipo": Unidade.TipoUnidade.INSPETORIA, "sigla": "IRF/SBO", "nome": "Inspetoria da Receita Federal em São Gabriel", "cidade": "São Gabriel"},
        ]

        criados = 0
        for item in unidades_data:
            _, created = Unidade.objects.get_or_create(
                sigla=item['sigla'],
                defaults={
                    'regiao_fiscal': rf10,
                    'tipo': item['tipo'],
                    'nome': item['nome'],
                    'cidade': item['cidade']
                }
            )
            if created:
                criados += 1

        self.stdout.write(self.style.SUCCESS(f"Sucesso! {criados} unidades da 10ª RF foram populadas."))