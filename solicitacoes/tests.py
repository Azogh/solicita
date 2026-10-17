from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Usuario, Unidade, RegiaoFiscal
from solicitacoes.models import OrdemServico


class SolicitaWorkflowTests(TestCase):

    def setUp(self):
        # 1. Criar Região Fiscal com código numérico (10)
        self.regiao = RegiaoFiscal.objects.create(
            nome="10ª Região Fiscal",
            codigo=10
        )
        
        # 2. Criar Unidade vinculada à Região Fiscal
        self.unidade = Unidade.objects.create(
            nome="Inspetoria São Borja",
            sigla="IRF/SBJ",
            regiao_fiscal=self.regiao
        )
        
        # 3. Criar Usuário Solicitante
        self.solicitante = Usuario.objects.create_user(
            username="solicitante_teste",
            password="SenhaSegura123",
            perfil=Usuario.PerfilChoices.SOLICITANTE,
            unidade=self.unidade
        )
        
        # 4. Criar Usuário Gestor
        self.gestor = Usuario.objects.create_user(
            username="gestor_teste",
            password="SenhaSegura123",
            perfil=Usuario.PerfilChoices.GESTOR
        )
        self.gestor.unidades_gerenciadas.add(self.unidade)

        self.client = Client()

    def test_criacao_ordem_servico(self):
        """ Testa a criação de uma nova OS via formulário """
        self.client.login(username="solicitante_teste", password="SenhaSegura123")
        
        response = self.client.post(reverse('criar_os'), {
            'assunto': 'Manutenção de Ar-Condicionado',
            'descricao': 'Aparelho do gabinete sem refrigeração.',
            'prioridade': 'URGENTE',
            'btn_enviar': '1'
        })
        
        self.assertEqual(response.status_code, 302)  # Redireciona após salvar
        self.assertEqual(OrdemServico.objects.count(), 1)
        
        os_criada = OrdemServico.objects.first()
        self.assertEqual(os_criada.status, OrdemServico.StatusChoices.ENVIADO)

    def test_restricao_acesso_gestor(self):
        """ Garante que Solicitante não acessa a central de relatórios do Gestor """
        self.client.login(username="solicitante_teste", password="SenhaSegura123")
        response = self.client.get(reverse('central_relatorios_dmr'))
        
        # Deve redirecionar de volta para o dashboard
        self.assertEqual(response.status_code, 302)