from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views
from solicitacoes import views as solicitacoes_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', accounts_views.landing_page_view, name='landing'),
    path('dashboard/', accounts_views.dashboard_view, name='dashboard'),
    
    # Login
    path('accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    
    path('registro/', accounts_views.registro_view, name='registro'),
    path('perfil/', accounts_views.perfil_view, name='perfil'),
    path('solicitar-elevacao-gestor/', accounts_views.solicitar_elevacao_gestor_view, name='solicitar_elevacao_gestor'),
    path('buscar-unidades/', accounts_views.buscar_unidades_view, name='buscar_unidades'),
    path('buscar-unidades-checkbox/', accounts_views.buscar_unidades_checkbox_view, name='buscar_unidades_checkbox'),
    
    # Rotas de OS, Feedbacks e DMR
    path('os/nova/', solicitacoes_views.criar_os_view, name='criar_os'),
    path('os/<int:pk>/editar/', solicitacoes_views.editar_os_view, name='editar_os'),
    path('os/<int:pk>/', solicitacoes_views.detalhar_os_view, name='detalhar_os'),
    path('os/<int:pk>/analisar/', solicitacoes_views.analisar_os_gestor_view, name='analisar_os'),
    path('cronograma/', solicitacoes_views.cronograma_visitas_view, name='cronograma_visitas'),
    path('feedback/novo/', solicitacoes_views.criar_feedback_dmr_view, name='criar_feedback_dmr'),
    path('feedback/novo/<int:os_id>/', solicitacoes_views.criar_feedback_dmr_view, name='criar_feedback_dmr_os'),
    path('feedbacks/', solicitacoes_views.listar_feedbacks_dmr_view, name='listar_feedbacks_dmr'),
    path('dmr/mensal/', solicitacoes_views.criar_relatorio_dmr_mensal_view, name='criar_relatorio_dmr_mensal'),
    path('dmr/central/', solicitacoes_views.central_relatorios_dmr_view, name='central_relatorios_dmr'),
    path('dmr/<int:pk>/detalhes/', solicitacoes_views.detalhar_relatorio_dmr_view, name='detalhar_relatorio_dmr'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)