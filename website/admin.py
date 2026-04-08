from django.contrib import admin
from .models import Operateur, GammeOperation, OrdreFabrication, OperationOF, Alea

# Permet de gérer tout depuis /admin sans coder d'interface au début

@admin.register(OrdreFabrication)
class OFAdmin(admin.ModelAdmin):
    list_display  = ['numero', 'produit', 'statut', 'date_due', 'avancement']
    list_filter   = ['statut']
    search_fields = ['numero', 'produit']

@admin.register(OperationOF)
class OperationOFAdmin(admin.ModelAdmin):
    list_display = ['of', 'gamme_operation', 'statut', 'heure_debut', 'heure_fin', 'operateur']
    list_filter  = ['statut']

@admin.register(Alea)
class AleaAdmin(admin.ModelAdmin):
    list_display = ['operation', 'type_alea', 'duree', 'declare_par', 'cree_le']

admin.site.register(Operateur)
admin.site.register(GammeOperation)