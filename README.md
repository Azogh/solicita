# Solicita — Sistema de Gestão de Ordens de Serviço (OS) & Fiscalização de Contratos

![Django](https://img.shields.io/badge/Django-5.2.18-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.15-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![Version](https://img.shields.io/badge/Version-v1.0.0-blue?style=for-the-badge)

O **Solicita** é uma plataforma centralizada desenvolvida para gerenciamento, acompanhamento e fiscalização de Ordens de Serviço (OS) de manutenção predial e apoio logístico no âmbito da Receita Federal do Brasil, integrando a comunicação entre as unidades solicitantes e os gestores regionais de contrato.

---

## 📌 Funcionalidades Principais

### 🔹 Perfil Solicitante (Unidades / Repartições)
- **Abertura de Chamados:** Cadastro rápido de solicitações com especificação de prioridade e anexos fotográficos.
- **Acompanhamento em Tempo Real:** Status atualizado do atendimento (Rascunho, Enviado, Em Atendimento e Concluído).
- **Emissão do DMR Mensal:** Preenchimento do Demonstrativo de Mensuração do Resultado com avaliação de desempenho da prestadora.
- **Download do DMR Individual em PDF:** Exportação nativa formatada em folha A4.

### 🔹 Perfil Gestor Regional (Fiscal de Contrato)
- **Painel de Análise Executiva:** Triagem e parecer técnico sobre os chamados das unidades jurisdicionadas.
- **Grade Semanal de Visitas:** Alocação de equipes técnicas por data com botão de impressão e exportação em PDF.
- **Central de Relatórios DMR / IMR:** Visualização regional da taxa de emissão por unidade e alerta de pendências do mês.
- **Download em Lote de DMRs:** Seleção por checkbox para download compilado de múltiplos relatórios (1 relatório por página).
- **IMR Consolidado da Jurisdição:** Relatório sintético regional para encaminhamento à comissão e instrução de pagamento.

### 🎨 Design & Usabilidade
- Interface responsiva focada no padrão institucional (Azul, Branco e Cinza).
- Suporte nativo ao **Modo Noturno (Dark Mode)** com persistência de tema no navegador.

---

## 🛠️ Tecnologias Utilizadas

- **Back-end:** Python, Django (v5.2.18)
- **Front-end:** HTML5, CSS3, JavaScript, Bootstrap 5, FontAwesome 6
- **Geração de Documentos:** `xhtml2pdf` (Renderização nativa de HTML para PDF)
- **Banco de Dados:** SQLite (Desenvolvimento/Testes)
- **Controle de Versão:** Git & GitHub

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
- Python 3.10+
- Git

### Passo a Passo

1. **Clonar o Repositório:**
   ```bash
   git clone [https://github.com/Azogh/solicita.git](https://github.com/Azogh/solicita.git)
   cd solicita

2. **Criar e Ativar o Ambiente Virtual (.venv):**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate

3. **Instalar as Dependências:**
   ```bash
   pip install -r requisitos.txt

4. **Executar as Migrações do Banco de Dados:**
    ```bash
   python manage.py migrate
   
6. **Iniciar o Servidor de Desenvolvimento:**
   ```bash
   python manage.py runserver

## 🧪 Testes Automatizados
O projeto conta com testes de integração cobrindo fluxos de permissão e criação de solicitações. Para executar a suíte de testes:
   ```bash
   python manage.py test solicitacoes
 ```

---

## 🏷️ Versionamento e Releases

- **`v1.0.0` (Release Oficial):**
  - Implementação completa do workflow de Ordens de Serviço (OS).
  - Grade semanal de visitas com exportação nativa em PDF.
  - Central DMR/IMR com suporte a download em lote e relatório consolidado da jurisdição.
  - Redesign minimalista da Landing Page e suporte ao Modo Noturno (Dark Mode).

---

## 👤 Autor

**André Gustavo Silva Ozga**
- **GitHub:** [@Azogh](https://github.com/Azogh)
- **LinkedIn:** [Perfil Profissional](https://linkedin.com/in/)

---

## ☕ Apoie o Desenvolvedor

Se este sistema foi útil para você ou para a sua instituição e você gostaria de apoiar a continuidade de projetos de código aberto, considere me pagar um café! ☕

[![Apoie com Pix](https://img.shields.io/badge/Apoie_com_Pix-00BD9D?style=for-the-badge&logo=pix&logoColor=white)](#-apoie-o-desenvolvedor)

> 🟢 **Chave Pix (Aleatória / E-mail):** `030677490-90`  
> *Sua contribuição ajuda a manter o desenvolvimento ativo e novos módulos!*