from django.contrib import admin
from .models import Operateur, GammeOperation, OrdreFabrication, OperationOF, Alea

# ===== ENREGISTREMENT SIMPLE DES MODÈLES =====
# Cela permet de gérer les données depuis l'interface admin Django
# http://localhost:8000/admin/

# Enregistrer Operateur
admin.site.register(Operateur)

# Enregistrer GammeOperation
admin.site.register(GammeOperation)

# Enregistrer OrdreFabrication
admin.site.register(OrdreFabrication)

# Enregistrer OperationOF
admin.site.register(OperationOF)

# Enregistrer Alea
admin.site.register(Alea)