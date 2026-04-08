from django.db import models
from django.utils import timezone

# ─── Opérateur ───────────────────────────────────────────────
# Représente un opérateur de l'atelier identifié par son badge
class Operateur(models.Model):
    nom        = models.CharField(max_length=100)
    prenom     = models.CharField(max_length=100)
    # code_badge = ce que lit le scanner code-barres
    code_badge = models.CharField(max_length=50, unique=True)
    poste      = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.code_badge})"


# ─── Gamme opératoire ─────────────────────────────────────────
# Définit une opération "type" avec son temps alloué standard
# Ex : "Assemblage structure" = 2,01h → 121 minutes
class GammeOperation(models.Model):
    nom           = models.CharField(max_length=200)
    # temps_alloue en minutes (plus pratique que les heures décimales)
    temps_alloue  = models.PositiveIntegerField(help_text="Durée standard en minutes")
    ordre         = models.PositiveSmallIntegerField(help_text="Position dans la gamme")

    class Meta:
        ordering = ['ordre']  # toujours triées dans l'ordre de la gamme

    def __str__(self):
        return f"{self.ordre}. {self.nom} ({self.temps_alloue} min)"


# ─── Ordre de Fabrication ─────────────────────────────────────
# Un OF = un strapontin (ou un lot) à produire
class OrdreFabrication(models.Model):

    STATUT_CHOICES = [
        ('en_attente',  'En attente'),
        ('en_cours',    'En cours'),
        ('en_retard',   'En retard'),
        ('termine',     'Terminé'),
        ('bloque',      'Bloqué'),
    ]

    numero          = models.CharField(max_length=50, unique=True)
    produit         = models.CharField(max_length=200)  # ex : "Strapontin modèle X"
    quantite        = models.PositiveIntegerField(default=1)
    date_lancement  = models.DateTimeField(default=timezone.now)
    date_due        = models.DateTimeField(help_text="Date de livraison prévue")
    statut          = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    # gamme = la liste des opérations prévues pour cet OF
    gamme           = models.ManyToManyField(GammeOperation, through='OperationOF')

    def __str__(self):
        return f"OF {self.numero} — {self.produit}"

    def est_en_retard(self):
        """Retourne True si l'OF n'est pas terminé et dépasse sa date due"""
        return self.statut != 'termine' and timezone.now() > self.date_due

    def avancement(self):
        """Calcule le % d'avancement : nb opérations pointées / nb total"""
        total   = self.operationof_set.count()
        terminees = self.operationof_set.filter(statut='termine').count()
        if total == 0:
            return 0
        return round((terminees / total) * 100)


# ─── Opération d'un OF ────────────────────────────────────────
# Liaison entre un OF et une GammeOperation
# C'est ici qu'on stocke l'état RÉEL de chaque opération
class OperationOF(models.Model):

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours',   'En cours'),
        ('termine',    'Terminé'),
        ('bloque',     'Bloqué'),
    ]

    of              = models.ForeignKey(OrdreFabrication, on_delete=models.CASCADE)
    gamme_operation = models.ForeignKey(GammeOperation, on_delete=models.CASCADE)
    statut          = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    # heure_debut et heure_fin = remplies automatiquement par le scan
    heure_debut     = models.DateTimeField(null=True, blank=True)
    heure_fin       = models.DateTimeField(null=True, blank=True)
    operateur       = models.ForeignKey(Operateur, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['gamme_operation__ordre']

    def temps_reel_minutes(self):
        """Calcule la durée réelle en minutes si l'opération est terminée"""
        if self.heure_debut and self.heure_fin:
            delta = self.heure_fin - self.heure_debut
            return round(delta.total_seconds() / 60)
        return None

    def est_en_retard(self):
        """Compare le temps réel au temps alloué"""
        tr = self.temps_reel_minutes()
        if tr and tr > self.gamme_operation.temps_alloue:
            return True
        return False

    def __str__(self):
        return f"{self.of.numero} / {self.gamme_operation.nom}"


# ─── Aléa (Muda / Incident) ──────────────────────────────────
# Enregistre tout ce qui perturbe le flux : attente, panne, déplacement inutile...
class Alea(models.Model):

    TYPE_CHOICES = [
        ('attente',          'Attente'),
        ('deplacement',      'Déplacement inutile'),
        ('panne',            'Panne machine'),
        ('manque_matiere',   'Manque matière'),
        ('rebus',            'Rebus / non-conformité'),
        ('autre',            'Autre'),
    ]

    operation   = models.ForeignKey(OperationOF, on_delete=models.CASCADE)
    type_alea   = models.CharField(max_length=30, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    # durée de l'aléa en minutes → permet de calculer le temps perdu total
    duree       = models.PositiveIntegerField(help_text="Durée en minutes", default=0)
    declare_par = models.ForeignKey(Operateur, null=True, blank=True, on_delete=models.SET_NULL)
    cree_le     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_alea_display()} sur {self.operation} ({self.duree} min)"