from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views
from solicitacoes import views as solicitacoes_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', accounts_views.landing_page_view, name='landing'),
    path('dashboard/', accounts_views.dashboard_view, name='dashboard'),
    path('registro/', accounts_views.registro_view, name='registro'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('perfil/', accounts_views.perfil_view, name='perfil'),
    path('perfil/solicitar-gestor/', accounts_views.solicitar_elevacao_gestor_view, name='solicitar_elevacao_gestor'),
    
    # Rotas de Ordens de Serviço
    path('os/nova/', solicitacoes_views.criar_os_view, name='criar_os'),
    path('os/<int:pk>/', solicitacoes_views.detalhar_os_view, name='detalhar_os'),
    path('os/<int:pk>/editar/', solicitacoes_views.editar_os_view, name='editar_os'),
    path('os/<int:pk>/analisar/', solicitacoes_views.analisar_os_gestor_view, name='analisar_os'),
    path('cronograma/', solicitacoes_views.cronograma_visitas_view, name='cronograma_visitas'),
    
    path('accounts/buscar-unidades/', accounts_views.buscar_unidades_view, name='buscar_unidades'),
    path('accounts/buscar-unidades-checkbox/', accounts_views.buscar_unidades_checkbox_view, name='buscar_unidades_checkbox'),

    path('feedback/novo/', solicitacoes_views.criar_feedback_dmr_view, name='criar_feedback_dmr'),
    path('feedback/novo/<int:os_id>/', solicitacoes_views.criar_feedback_dmr_view, name='criar_feedback_dmr_os'),
    path('feedbacks/', solicitacoes_views.listar_feedbacks_dmr_view, name='listar_feedbacks_dmr'),
]