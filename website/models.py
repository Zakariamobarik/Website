from django.db import models
from django.utils import timezone
from datetime import timedelta

# ─── Opérateur ───────────────────────────────────────────────
class Operateur(models.Model):
    nom        = models.CharField(max_length=100)
    prenom     = models.CharField(max_length=100)
    code_badge = models.CharField(max_length=50, unique=True)
    poste      = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.code_badge})"


# ─── Gamme opératoire ─────────────────────────────────────────
class GammeOperation(models.Model):
    nom           = models.CharField(max_length=200)
    temps_alloue  = models.DecimalField(max_digits=5, decimal_places=2, help_text="Durée standard en minutes")
    ordre         = models.PositiveSmallIntegerField(help_text="Position dans la gamme")

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return f"{self.ordre}. {self.nom} ({self.temps_alloue} min)"


# ─── Ordre de Fabrication (SIMPLIFIÉ) ──────────────────────────────
class OrdreFabrication(models.Model):
    """
    SIMPLIFIÉ:
    - Pas de date_lancement (on sait pas quand ça commence)
    - Pas de date_due (on sait pas la date de livraison à l'avance)
    - Pas de statut (calculé automatiquement)
    - Pas de gamme ManyToMany (les OperationOF font le lien)
    """

    numero   = models.CharField(max_length=50, unique=True)
    produit  = models.CharField(max_length=200)
    quantite = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"OF {self.numero} — {self.produit}"

    # ✅ MÉTHODE CORRIGÉE
    @property
    def avancement(self):
        """
        Calcule le % d'avancement en comptant les opérations terminées
        """
        # Récupère toutes les opérations de cet OF
        operations = self.operationof_set.all()
        total = operations.count()
        
        if total == 0:
            return 0
        
        # Compte les opérations terminées (statut='termine')
        terminees = 0
        for op in operations:
            # ✅ On lit la @property statut, on ne la filtre pas
            if op.statut == 'termine':
                terminees += 1
        
        # Retourne le pourcentage
        return round((terminees / total) * 100)

    @property
    def premiere_entree(self):
        """Date d'entrée de la première opération"""
        first = self.operationof_set.order_by('gamme_operation__ordre').first()
        return first.date_entree if first else None

    @property
    def derniere_sortie(self):
        """Date de sortie de la dernière opération"""
        last = self.operationof_set.order_by('gamme_operation__ordre').last()
        return last.date_sortie if last else None

    @property
    def temps_total_reel(self):
        """Calcule le temps TOTAL réel de production"""
        if self.premiere_entree and self.derniere_sortie:
            delta = self.derniere_sortie - self.premiere_entree
            return round(delta.total_seconds() / 60)
        return None

    # ✅ AJOUTER CES 3 PROPRIÉTÉS:
    @property
    def temps_total_theorique(self):
        """
        Temps THÉORIQUE = somme de tous les temps alloués
        C'est le temps idéal sans retards
        """
        operations = self.operationof_set.all()
        
        if not operations.exists():
            return 0
        
        total = 0
        for op in operations:
            total += float(op.gamme_operation.temps_alloue)
        
        return round(total)

    @property
    def heure_fin_prevue(self):
        """
        Heure de fin PRÉVUE = première entrée + temps théorique
        """
        if not self.premiere_entree:
            return None
        
        temps_theo = self.temps_total_theorique
        return self.premiere_entree + timedelta(minutes=temps_theo)

    @property
    def ecart_temps(self):
        """
        ÉCART = temps réel - temps théorique
        Positif = dépassement (en retard)
        Négatif = gain de temps (en avance)
        """
        if not self.temps_total_reel:
            return None
        
        return self.temps_total_reel - self.temps_total_theorique


# ─── -----------------------------Opération d'un OF --------------------------------------------------------------------------
class OperationOF(models.Model):

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours',   'En cours'),
        ('termine',    'Terminé'),
        ('bloque',     'Bloqué'),
    ]

    of              = models.ForeignKey(OrdreFabrication, on_delete=models.CASCADE)
    gamme_operation = models.ForeignKey(GammeOperation, on_delete=models.CASCADE)
    
    date_entree     = models.DateTimeField(null=True, blank=True, help_text="Date/heure d'ENTRÉE (saisie manuelle)")
    operateur       = models.ForeignKey(Operateur, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['gamme_operation__ordre']
        unique_together = ('of', 'gamme_operation')

    def __str__(self):
        return f"{self.of.numero} / {self.gamme_operation.nom}"

    # 🔑 PROPRIÉTÉ 1: Date de sortie (CALCULÉE AUTO)
    @property
    def date_sortie(self):
        """date_sortie = date_entree + temps_alloue"""
        if not self.date_entree:
            return None
        temps_minutes = float(self.gamme_operation.temps_alloue)
        return self.date_entree + timedelta(minutes=temps_minutes)

    # 🔑 PROPRIÉTÉ 2: STATUT AUTOMATIQUE !!!
    @property
    def statut(self):
        """
        🔥 LE STATUT EST CALCULÉ AUTOMATIQUEMENT:
        
        - Si date_entree n'existe pas → 'en_attente'
        - Si l'heure actuelle < date_sortie → 'en_cours'
        - Si l'heure actuelle >= date_sortie → 'termine' ✅
        """
        from django.utils import timezone
        
        # Pas encore commencée
        if not self.date_entree:
            return 'en_attente'
        
        # Déjà commencée, on compare avec maintenant
        maintenant = timezone.now()
        
        # Si on a dépassé la date de sortie → TERMINÉE!
        if self.date_sortie and maintenant >= self.date_sortie:
            return 'termine'
        
        # Sinon, c'est en cours
        return 'en_cours'

    # 🔑 PROPRIÉTÉ 3: Temps réel en minutes
    @property
    def temps_reel_minutes(self):
        """Durée réelle"""
        if self.date_entree and self.date_sortie:
            delta = self.date_sortie - self.date_entree
            return round(delta.total_seconds() / 60)
        return None

    # 🔑 PROPRIÉTÉ 4: Est terminée ?
    @property
    def est_terminee(self):
        """Retourne True si l'opération est terminée"""
        return self.statut == 'termine'
    
    # ✅ AJOUTER: Propriété 5: retard_minutes
    @property
    def retard_minutes(self):
        """Retard = date_entree(n) - date_sortie(n-1)"""
        if not self.date_entree:
            return None
        
        operation_precedente = OperationOF.objects.filter(
            of=self.of,
            gamme_operation__ordre__lt=self.gamme_operation.ordre
        ).order_by('-gamme_operation__ordre').first()
        
        if not operation_precedente:
            return 0
        
        if not operation_precedente.date_sortie:
            return None
        
        delta = self.date_entree - operation_precedente.date_sortie
        return round(delta.total_seconds() / 60)
    
    # ✅ GARDER: Propriété 6: retard_minutes_affichage
    @property
    def retard_minutes_affichage(self):
        """Affiche le retard de l'opération suivante"""
        operation_suivante = OperationOF.objects.filter(
            of=self.of,
            gamme_operation__ordre=self.gamme_operation.ordre + 1
        ).first()
        
        if not operation_suivante:
            return None
        
        return operation_suivante.retard_minutes
    
    # ✅ GARDER: Propriété 7: statut_retard
    @property
    def statut_retard(self):
        """Retourne 'retard', 'avance', ou 'normal'"""
        r = self.retard_minutes
        if r is None:
            return None
        if r > 0:
            return 'retard'
        elif r < 0:
            return 'avance'
        else:
            return 'normal'


# ─── Aléa ─────────────────────────────────────────────────────
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
    duree       = models.PositiveIntegerField(help_text="Durée en minutes", default=0)
    declare_par = models.ForeignKey(Operateur, null=True, blank=True, on_delete=models.SET_NULL)
    cree_le     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_alea_display()} sur {self.operation} ({self.duree} min)"