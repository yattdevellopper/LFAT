from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError
from django.utils import timezone # Pour les dates/heures actuelles




# ====================================================================
# PARAMÈTRES ET GESTION INSTITUTIONNELLE
# ====================================================================

# Modèle pour les paramètres généraux de l'école (incluant les assets pour les documents : Logo, Cachet, Signature)

from django.db import models




class EcoleSettings(models.Model):
    """
    Configuration d'une école (multi-instances autorisées)
    """
    # ⚠️ Suppression du champ unique_instance et du clean() restrictif
    # Chaque école aura désormais sa propre configuration

    # Informations institutionnelles
    ministere = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Ministère de Tutelle",
        help_text="Exemple : Ministère de l’Éducation Nationale"
    )
    academie = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Académie / Inspection",
        help_text="Exemple : Académie de Bamako Rive Droite"
    )
    commune = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Commune",
        help_text="Exemple : Commune IV du District de Bamako"
    )

    # Informations de l’établissement
    nom_etablissement = models.CharField(
        max_length=255,
        verbose_name="Nom de l'Établissement"
    )
    adresse_etablissement = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Adresse"
    )
    telephone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Téléphone de l'Établissement"
    )
    email_contact = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email de Contact"
    )
    site_web = models.URLField(
        blank=True,
        null=True,
        verbose_name="Site Web"
    )

    # Identifiants administratifs
    code_etablissement = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,  # ✅ Chaque école doit avoir un code unique
        verbose_name="Code de l'Établissement",
        help_text="Code attribué par le ministère ou la direction académique"
    )

    # Éléments graphiques pour les documents officiels
    logo = models.ImageField(
        upload_to='settings/assets/',
        blank=True,
        null=True,
        verbose_name="Logo de l'École"
    )
    cachet_admin = models.ImageField(
        upload_to='settings/assets/',
        blank=True,
        null=True,
        verbose_name="Cachet (Sceau) de l'Administration"
    )
    signature_directeur = models.ImageField(
        upload_to='settings/assets/',
        blank=True,
        null=True,
        verbose_name="Signature du Directeur/Responsable"
    )

    titre_signataire = models.CharField(
        max_length=100,
        default='Le Directeur',
        verbose_name="Titre du Signataire"
    )
    nom_signataire = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nom du Signataire",
        help_text="Nom du directeur ou responsable signataire"
    )

    date_mise_a_jour = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )

    class Meta:
        verbose_name = "École"
        verbose_name_plural = "Écoles"
        ordering = ['nom_etablissement']

     # ⚡ Période d'essai gratuite et activation
    date_fin_essai = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fin de la période d'essai gratuite"
    )
    est_active = models.BooleanField(
        default=True,
        verbose_name="École active",
        help_text="Indique si l'école peut utiliser le système"
    )

    def save(self, *args, **kwargs):
        # Si création, définir la fin de la période d'essai à 30 jours
        if not self.pk:
            self.date_fin_essai = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)

    def periode_essai_expiree(self):
        """Retourne True si la période d'essai est terminée"""
        return self.date_fin_essai and timezone.now() > self.date_fin_essai

    # Optionnel : vérifier si l'école peut utiliser le système
    def peut_utiliser_systeme(self):
        return self.est_active or not self.periode_essai_expiree()


    def __str__(self):
        return f"{self.nom_etablissement} ({self.code_etablissement or 'Sans code'})"
    


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ecole = models.ForeignKey("EcoleSettings", on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} "



# Modèle pour l'année scolaire (très important pour filtrer les données)
from django.db import models
class AnneeScolaire(models.Model):
    ecole = models.ForeignKey(
        'EcoleSettings',
        on_delete=models.CASCADE,
        verbose_name="École"
    )
    
    annee = models.CharField(
        max_length=9,
        verbose_name="Année Scolaire",
        help_text="Exemple : 2024-2025"
    )
    date_debut = models.DateField(verbose_name="Date de Début")
    date_fin = models.DateField(verbose_name="Date de Fin")
    active = models.BooleanField(
        default=False,
        verbose_name="Active (Année en cours)",
        help_text="Si cochée, cette année sera considérée comme l'année scolaire en cours."
    )

    class Meta:
        verbose_name = "Année Scolaire"
        verbose_name_plural = "Années Scolaires"
        ordering = ['-annee']  # Affiche l'année la plus récente en premier
        unique_together = ('ecole', 'annee')  # Unicité par école

    def __str__(self):
        return f"{self.annee} ({self.ecole})"

    def save(self, *args, **kwargs):
        # Si on active cette année, désactiver les autres pour la même école
        super().save(*args, **kwargs)  # On sauvegarde d'abord pour avoir un pk
        if self.active:
            AnneeScolaire.objects.filter(ecole=self.ecole, active=True).exclude(pk=self.pk).update(active=False)




# ====================================================================
# PERSONNEL
# ====================================================================

# Modèle pour les enseignants
class Enseignant(models.Model):
    ecole = models.ForeignKey(
     'EcoleSettings',
     on_delete=models.CASCADE,
     verbose_name="École",
     default=1,
     related_name='enseignants')  # <-- ajoute ce related_name


    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Utilisateur Django")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    contact = models.CharField(max_length=50, blank=True, null=True, verbose_name="Contact Téléphonique")
    email = models.EmailField(blank=True, null=True, verbose_name="Adresse Email")
    specialite = models.CharField(max_length=100, blank=True, null=True, verbose_name="Spécialité/Matière principale")

    class Meta:
        verbose_name = "Enseignant"
        verbose_name_plural = "Enseignants"
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.prenom} {self.nom}"


# ====================================================================
# STRUCTURE SCOLAIRE
# ====================================================================

# Modèle pour les classes (avec niveau et série si applicable)
class Classe(models.Model):
    ecole = models.ForeignKey(
        'EcoleSettings',
        on_delete=models.CASCADE,
        verbose_name="École",
        default=1)
    
    nom_classe = models.CharField(max_length=100, verbose_name="Nom de la Classe") # Ex: "7ème Année A", "Terminale L"
    niveau = models.CharField(max_length=50, verbose_name="Niveau Scolaire",
                              choices=[
                                  ('1AP', '1ère Année Fondamentale'), ('2AP', '2ème Année Fondamentale'),
                                  ('3AP', '3ème Année Fondamentale'), ('4AP', '4ème Année Fondamentale'),
                                  ('5AP', '5ème Année Fondamentale'), ('6AP', '6ème Année Fondamentale'),
                                  ('7AP', '7ème Année Fondamentale'), ('8AP', '8ème Année Fondamentale'),
                                  ('9AP', '9ème Année Fondamentale'),
                                  ('1AS', '1ère Année Secondaire'), ('2AS', '2ème Année Secondaire'),
                                  ('TL', 'Terminale L'), ('TS', 'Terminale S'), ('TC', 'Terminale C'),
                              ])
    serie = models.CharField(max_length=50, blank=True, null=True, verbose_name="Série (pour le Secondaire)")
    enseignant_principal = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True,related_name='classes_principales', verbose_name= "Enseignant Principal")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année Scolaire")

    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        unique_together = ('nom_classe', 'annee_scolaire')
        ordering = ['annee_scolaire', 'niveau', 'nom_classe']

    def __str__(self):
        return f"{self.nom_classe} ({self.annee_scolaire.annee})"

# Modèle pour les matières
class Matiere(models.Model):
    ecole = models.ForeignKey(
        'EcoleSettings',
        on_delete=models.CASCADE,
        verbose_name="École",
        default=1)
    
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom de la Matière")
    code_matiere = models.CharField(max_length=10, unique=True, blank=True, null=True, verbose_name="Code Matière")

    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
        ordering = ['nom']

    def __str__(self):
        return self.nom

# Modèle pour lier les matières aux classes avec leur coefficient
class ProgrammeMatiere(models.Model):
    ecole = models.ForeignKey(
        'EcoleSettings',
        on_delete=models.CASCADE,
        verbose_name="École",
        default=1)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, verbose_name="Classe")
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, verbose_name="Matière")
    enseignant = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Enseignant de la matière")
    coefficient = models.IntegerField(default=1, verbose_name="Coefficient")

    class Meta:
        verbose_name = "Programme Matière par Classe"
        verbose_name_plural = "Programmes Matières par Classe"
        unique_together = ('classe', 'matiere')
        ordering = ['classe', 'matiere__nom']

    def __str__(self):
        return f"{self.matiere.nom} ({self.coefficient}) en {self.classe.nom_classe}"


# ====================================================================
# ÉTUDIANTS / ÉLÈVES ET INSCRIPTION
# ====================================================================

# Modèle pour les étudiants/élèves
class Etudiant(models.Model):
    ecole = models.ForeignKey(
        'EcoleSettings',
        on_delete=models.CASCADE,
        verbose_name="École",
        default=1)
    SEXE_CHOICES = [('M', 'Masculin'), ('F', 'Féminin')]
    SITUATION_CHOICES = [('Actif', 'Actif'), ('Ancien', 'Ancien'), ('Suspendu', 'Suspendu'), ('Radié', 'Radié')]

    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom(s)")
    date_naissance = models.DateField(verbose_name="Date de Naissance")
    lieu_naissance = models.CharField(max_length=100, blank=True, null=True, verbose_name="Lieu de Naissance")
    genre = models.CharField(max_length=1, choices=SEXE_CHOICES, verbose_name="Sexe")
    nationalite = models.CharField(max_length=50, default='Malienne', verbose_name="Nationalité")
    adresse = models.CharField(max_length=200, blank=True, null=True, verbose_name="Adresse Résidentielle")
    ville = models.CharField(max_length=100, default='Bamako', verbose_name="Ville")
    contact_parent = models.CharField(max_length=50, blank=True, null=True, verbose_name="Contact Parent/Tuteur")
    email_parent = models.EmailField(blank=True, null=True, verbose_name="Email Parent/Tuteur")
    numero_matricule = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Numéro Matricule")
    
    classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Classe Actuelle")
    annee_scolaire_inscription = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année d'Inscription")
    date_inscription = models.DateField(default=timezone.now, verbose_name="Date d'Inscription")
    photo_profil = models.ImageField(upload_to='photos_profil_eleves/', blank=True, null=True, verbose_name="Photo de Profil")
    statut = models.CharField(max_length=20, choices=SITUATION_CHOICES, default='Actif', verbose_name="Statut Actuel")


    class Meta:
        verbose_name = "Élève"
        verbose_name_plural = "Élèves"
        ordering = ['classe__nom_classe', 'nom', 'prenom']

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.classe.nom_classe if self.classe else 'Non assigné'})"

# Modèle pour les photos des dossiers d'inscription
class DossierInscriptionImage(models.Model):
    ecole = models.ForeignKey(
        'EcoleSettings',
        on_delete=models.CASCADE,
        verbose_name="École",
        default=1)
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='dossier_images', verbose_name="Élève")
    image = models.ImageField(upload_to='dossiers_inscription/', verbose_name="Fichier (Image ou PDF)")
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Description du document")
    date_telechargement = models.DateTimeField(auto_now_add=True, verbose_name="Date de Téléchargement")

    class Meta:
        verbose_name = "Document d'Inscription"
        verbose_name_plural = "Documents d'Inscription"
        ordering = ['etudiant', 'description']

    def __str__(self):
        return f"Dossier de {self.etudiant} - {self.description or 'Document'}"


# ====================================================================
# NOTES ET ÉVALUATIONS
# ====================================================================

# Modèle pour les notes des élèves
class Note(models.Model):
    ecole = models.ForeignKey(
        'EcoleSettings',
        on_delete=models.CASCADE,
        verbose_name="École",
        default=1)
    
    PERIODE_EVALUATION_CHOICES = [
        ('Trimestre 1', 'Trimestre 1'), ('Trimestre 2', 'Trimestre 2'),
        ('Trimestre 3', 'Trimestre 3'), ('Annuelle', 'Annuelle'),
    ]

    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='notes')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, verbose_name="Matière")
    valeur = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Note Obtenue (sur 20)")
    periode_evaluation = models.CharField(max_length=20, choices=PERIODE_EVALUATION_CHOICES, verbose_name="Période d'Évaluation")
    type_evaluation = models.CharField(max_length=50, blank=True, null=True, verbose_name="Type d'Évaluation")
    date_evaluation = models.DateField(default=timezone.now, verbose_name="Date de l'Évaluation")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année Scolaire")

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        unique_together = ('etudiant', 'matiere', 'periode_evaluation', 'annee_scolaire')
        ordering = ['annee_scolaire', 'etudiant', 'periode_evaluation', 'matiere__nom']

    def __str__(self):
        return f"{self.etudiant.prenom} {self.etudiant.nom} - {self.matiere.nom} ({self.periode_evaluation}): {self.valeur}/20"

    def get_coefficient(self):
        """Récupère le coefficient de la matière pour la classe de l'étudiant."""
        try:
            return ProgrammeMatiere.objects.get(classe=self.etudiant.classe, matiere=self.matiere).coefficient
        except ProgrammeMatiere.DoesNotExist:
            return 1


# ====================================================================
# FINANCES ET PAIEMENTS
# ====================================================================

# Modèle pour le suivi des paiements
class Paiement(models.Model):
    ecole = models.ForeignKey(
        'EcoleSettings',
        on_delete=models.CASCADE,
        verbose_name="École",
        default=1)
    
    STATUT_PAIEMENT_CHOICES = [('Payé', 'Payé'), ('Impayé', 'Impayé'), ('Partiel', 'Partiel')]
    MOTIF_PAIEMENT_CHOICES = [
        ('Frais de Scolarité', 'Frais de Scolarité'), ('Frais d\'Inscription', 'Frais d\'Inscription'),
        ('Cotisation APEM', 'Cotisation APEM'), ('Tenue Scolaire', 'Tenue Scolaire'),
        ('Repas Scolaire', 'Repas Scolaire'), ('Autres', 'Autres'),
    ]
    MODE_PAIEMENT_CHOICES = [
        ('Espèces', 'Espèces'), ('Chèque', 'Chèque'),
        ('Virement Bancaire', 'Virement Bancaire'), ('Mobile Money', 'Mobile Money'),
    ]

    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='paiements')
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant Payé (FCFA)")
    montant_du = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant Total Dû", blank=True, null=True)
    date_paiement = models.DateField(default=timezone.now, verbose_name="Date du Paiement")
    motif_paiement = models.CharField(max_length=100, choices=MOTIF_PAIEMENT_CHOICES, verbose_name="Motif du Paiement")
    statut = models.CharField(max_length=20, choices=STATUT_PAIEMENT_CHOICES, default='Payé', verbose_name="Statut du Paiement")
    mode_paiement = models.CharField(max_length=50, choices=MODE_PAIEMENT_CHOICES, verbose_name="Mode de Paiement")
    recu_numero = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Numéro de Reçu")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année Scolaire Concernée")
    enregistre_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Enregistré par")


    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-date_paiement', 'etudiant__nom']

    def __str__(self):
        return f"Paiement de {self.etudiant.prenom} {self.etudiant.nom} - {self.montant} FCFA ({self.statut})"


# ====================================================================
# ABSENCES ET PRÉSENCES
# ====================================================================

# Modèle pour le suivi des présences
class Presence(models.Model):
    ecole = models.ForeignKey(
        'EcoleSettings',
        on_delete=models.CASCADE,
        verbose_name="École",
        default=1)
    STATUT_PRESENCE_CHOICES = [
        ('Présent', 'Présent'), ('Absent', 'Absent'),
        ('Retard', 'Retard'), ('Excusé', 'Excusé'),
    ]

    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='presences')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, verbose_name="Classe concernée")
    date = models.DateField(verbose_name="Date de la Présence")
    statut = models.CharField(max_length=20, choices=STATUT_PRESENCE_CHOICES, verbose_name="Statut")
    matiere = models.ForeignKey(Matiere, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Matière (optionnel)")
    heure_debut_cours = models.TimeField(blank=True, null=True, verbose_name="Heure de Début du Cours")
    heure_fin_cours = models.TimeField(blank=True, null=True, verbose_name="Heure de Fin du Cours")
    motif_absence_retard = models.TextField(blank=True, null=True, verbose_name="Motif (si absent/retard)")
    justificatif_fourni = models.BooleanField(default=False, verbose_name="Justificatif Fourni ?")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année Scolaire")
    enregistre_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Enregistré par")


    class Meta:
        verbose_name = "Présence"
        verbose_name_plural = "Présences"
        unique_together = ('etudiant', 'date', 'matiere', 'annee_scolaire')
        ordering = ['-date', 'classe__nom_classe', 'etudiant__nom']

    def __str__(self):
        return f"{self.etudiant.prenom} {self.etudiant.nom} - {self.date} ({self.statut})"


# ====================================================================
# DOCUMENTS OFFICIELS
# ====================================================================

# Modèle pour les certificats de fréquentation (pour garder une trace des certificats générés)
# Les assets (logo, cachet, signature) sont récupérés via le modèle EcoleSettings lors de la génération.

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class CertificatFrequentation(models.Model):
    ecole = models.ForeignKey(
        'EcoleSettings',
        on_delete=models.CASCADE,
        verbose_name="École",
        default=1
    )
    etudiant = models.ForeignKey("dashboard.Etudiant", on_delete=models.CASCADE, verbose_name="Élève")
    annee_scolaire = models.ForeignKey("dashboard.AnneeScolaire", on_delete=models.CASCADE, verbose_name="Année Scolaire")
    date_delivrance = models.DateField(default=timezone.now, verbose_name="Date de Délivrance")
    numero_certificat = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Numéro du Certificat")
    lieu_delivrance = models.CharField(max_length=100, verbose_name="Lieu de délivrance", blank=True, null=True, default="Bamako")

    fichier_pdf = models.FileField(upload_to='certificats_frequentation/', blank=True, null=True, verbose_name="Fichier PDF du Certificat")
    delivre_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Délivré par")

    cachet_utilise = models.FileField(upload_to='certificats/assets/', blank=True, null=True, verbose_name="Cachet (Sceau) utilisé")
    signature_utilisee = models.FileField(upload_to='certificats/assets/', blank=True, null=True, verbose_name="Signature utilisée")

    ministere = models.CharField(max_length=255, default="MINISTÈRE DE L’ENSEIGNEMENT SUPÉRIEUR / ET DE LA RECHERCHE SCIENTIFIQUE", verbose_name="Ministère de tutelle")
    academie = models.CharField(max_length=255, default="Académie de Bamako Rive Droite", verbose_name="Académie / CAP")
    etablissement_reference = models.CharField(max_length=255, default="Complexe Scolaire Privé de Banankabougou", verbose_name="Nom de l’établissement complet")
    adresse_etablissement = models.CharField(max_length=255, default="Banankabougou, Bamako - Mali", verbose_name="Adresse complète de l’établissement")

    mention_legale = models.TextField(blank=True, null=True, verbose_name="Mention légale ou texte additionnel")
    qr_code = models.ImageField(upload_to='certificats/qrcodes/', blank=True, null=True, verbose_name="QR Code de vérification")
    code_verification = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="Code de vérification du document")

    statut = models.CharField(
        max_length=20,
        choices=[('valide', 'Valide'), ('annule', 'Annulé'), ('archive', 'Archivé')],
        default='valide',
        verbose_name="Statut du certificat"
    )
    remarque = models.TextField(blank=True, null=True, verbose_name="Remarque administrative")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Certificat de Fréquentation"
        verbose_name_plural = "Certificats de Fréquentation"
        unique_together = ('etudiant', 'annee_scolaire')
        ordering = ['-annee_scolaire', 'etudiant__nom']

    def __str__(self):
        return f"Certificat de {self.etudiant} ({self.annee_scolaire})"

    @property
    def nom_complet(self):
        return f"{self.etudiant.nom} {self.etudiant.prenom}"

    def is_valide(self):
        return self.statut == 'valide'

    def save(self, *args, **kwargs):
        if not self.numero_certificat:
            annee = self.date_delivrance.year if self.date_delivrance else timezone.now().year
            self.numero_certificat = f"CERT-{self.etudiant.numero_matricule or self.etudiant.pk}-{annee}"
        super().save(*args, **kwargs)

    



from django.db import models
# Assurez-vous d'importer vos modèles personnalisés (Classe, Matiere, Enseignant, AnneeScolaire)
# from .models import Classe, Matiere, Enseignant, AnneeScolaire 

class EmploiDuTemps(models.Model):
    ecole = models.ForeignKey(
        'EcoleSettings',
        on_delete=models.CASCADE,
        verbose_name="École",
        default=1)
    class JourSemaine(models.TextChoices):
        LUNDI = 'Lundi', ('Lundi')
        MARDI = 'Mardi', ('Mardi')
        MERCREDI = 'Mercredi', ('Mercredi')
        JEUDI = 'Jeudi', ('Jeudi')
        VENDREDI = 'Vendredi', ('Vendredi')
        SAMEDI = 'Samedi', ('Samedi')

    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='emplois_du_temps', verbose_name="Classe")
    jour = models.CharField(max_length=20, choices=JourSemaine.choices, verbose_name="Jour de la Semaine")
    
    # --- CHAMPS HEURES MODIFIÉS ---
    heure_debut = models.TimeField(verbose_name="Heure de Début")
    heure_fin = models.TimeField(verbose_name="Heure de Fin")
    # --- FIN CHAMPS HEURES MODIFIÉS ---
    emploiDuTemps = models.FileField(upload_to='emploiDuTemps/', blank=True, null=True, verbose_name="Fichier PDF demploi")

    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, verbose_name="Matière")
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, verbose_name="Enseignant")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année Scolaire")

    class Meta:
        # L'unicité est basée sur la classe, le jour et la PÉRIODE (début/fin) dans l'année scolaire
        unique_together = ('classe', 'jour', 'heure_debut', 'heure_fin', 'annee_scolaire')
        
        # Le tri doit être fait de manière séquentielle pour l'affichage dans un tableau
        ordering = ['classe', 'annee_scolaire', 'jour', 'heure_debut']

        verbose_name = "Emploi du Temps"
        verbose_name_plural = "Emplois du Temps"
        
    def __str__(self):
        # Affichage des heures au format HH:MM
        heure_str = f"{self.heure_debut.strftime('%H:%M')} - {self.heure_fin.strftime('%H:%M')}"
        return f"{self.classe.nom_classe} - {self.jour} {heure_str} : {self.matiere.nom}"

    # Vous pouvez ajouter une validation personnalisée pour s'assurer que heure_fin > heure_debut
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.heure_debut and self.heure_fin and self.heure_debut >= self.heure_fin:
            raise ValidationError("L'heure de fin doit être postérieure à l'heure de début.")



