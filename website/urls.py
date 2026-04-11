"""
Configuration des routes (URLs) de l'application
Les routes lient les URLs aux vues correspondantes
"""

from django.urls import path
from . import views

# Noms uniques des routes (utilisés dans les templates avec {% url 'nom' %})
urlpatterns = [
# ==================== AUTHENTIFICATION =======================================
    path('', views.home, name='home'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_user, name='logout'),
# ==================== AUTHENTIFICATION =======================================
    path('gammes/', views.gammes_list, name='gammes_list'),
    path('gamme/ajouter/', views.gamme_form, name='ajouter_gamme'),  # Ajouter (id=None)
    path('gamme/<int:id>/modifier/', views.gamme_form, name='modifier_gamme'),  # Modifier
    path('gamme/<int:id>/supprimer/', views.supprimer_gamme, name='supprimer_gamme'),  # Supprimer

# ==================== Opérateurs  =======================================

    path('operateurs/', views.operateurs_list, name='operateur_list'),
    path('operateur/ajouter/', views.operateur_form, name='ajouter_operateur'),
    path('operateur/<int:id>/modifier/', views.operateur_form, name='modifier_operateur'),
    path('operateur/<int:id>/supprimer/', views.supprimer_operateur, name='supprimer_operateur'),

# ==================== Ordre de fabrication  =======================================

    path('of/', views.of_list, name='of_list'),
    
    # Ajouter/modifier OF
    path('of/ajouter/', views.of_form, name='ajouter_of'),
    path('of/<int:id>/modifier/', views.of_form, name='modifier_of'),  
    # Supprimer OF
    path('of/<int:id>/supprimer/', views.supprimer_of, name='supprimer_of'),
    
    # Voir le détail d'un OF (timeline)
    path('of/<int:id>/detail/', views.of_detail, name='of_detail'),
    
    # Saisir l'entrée d'une opération
    path('operation/<int:operation_id>/entree/', views.saisir_entree_operation, name='saisir_entree_operation'),
    
    # Marquer une opération comme terminée (optionnel)
    path('operation/<int:operation_id>/terminer/', views.terminer_operation, name='terminer_operation'),
    
# ==================== Ordre de fabrication  =======================================

    path('statistiques/retard/', views.list_retard, name='list_retard'),



# ==================== next  =======================================




























    # ===== PRODUCTION / DASHBOARD =====
    path('dashboard-home/', views.dashboard_home, name='dashboard_home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ===== POINTAGE =====
    path('pointage/', views.pointage_view, name='pointage'),
    
    # ===== PAGES À CRÉER =====
    path('of/', views.of_list, name='of_list'),
    path('of/<str:numero_of>/', views.of_detail, name='detail_of'),
    path('gammes/', views.gammes_list, name='gammes_list'),
    path('alea/<int:operation_id>/', views.declarer_alea, name='declarer_alea'),
]

"""
REMARQUES:

1. L'ordre des routes compte
   - Les routes plus spécifiques doivent être avant les générales
   - Ex: /of/<numero_of>/ doit être avant une route /of/

2. Types de paramètres
   - <str:param> = Chaîne de caractères
   - <int:param> = Nombre entier
   - <slug:param> = Slug (lettres, chiffres, tirets, underscores)
   - <uuid:param> = UUID unique
   
3. Utilisation dans les templates
   - {% url 'dashboard' %} → /dashboard/
   - {% url 'detail_of' numero_of='OF-2024-001' %} → /of/OF-2024-001/
   
4. Redirection dans les vues
   - return redirect('dashboard') → redirige vers /dashboard/
   - return redirect('detail_of', numero_of='OF-001') → /of/OF-001/

5. Vérifier les accès
   - Utiliser @login_required décorateur dans views.py
   - Empêche l'accès aux utilisateurs non connectés
"""
