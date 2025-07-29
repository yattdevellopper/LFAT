from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone # Pour les dates/heures actuelles

# Modèle pour l'année scolaire (très important pour filtrer les données)
class AnneeScolaire(models.Model):
    annee = models.CharField(max_length=9, unique=True, verbose_name="Année Scolaire") # Ex: '2024-2025'
    date_debut = models.DateField(verbose_name="Date de Début")
    date_fin = models.DateField(verbose_name="Date de Fin")
    active = models.BooleanField(default=True, verbose_name="Active (Année en cours)") # Pour identifier l'année scolaire en cours

    class Meta:
        verbose_name = "Année Scolaire"
        verbose_name_plural = "Années Scolaires"
        ordering = ['-annee'] # Affiche l'année la plus récente en premier

    def __str__(self):
        return self.annee

# Modèle pour les enseignants
class Enseignant(models.Model):
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

# Modèle pour les classes (avec niveau et série si applicable)
class Classe(models.Model):
    nom_classe = models.CharField(max_length=100, verbose_name="Nom de la Classe") # Ex: "7ème Année A", "Terminale L"
    niveau = models.CharField(max_length=50, verbose_name="Niveau Scolaire",
                              choices=[
                                  ('1AP', '1ère Année Fondamentale'),
                                  ('2AP', '2ème Année Fondamentale'),
                                  ('3AP', '3ème Année Fondamentale'),
                                  ('4AP', '4ème Année Fondamentale'),
                                  ('5AP', '5ème Année Fondamentale'),
                                  ('6AP', '6ème Année Fondamentale'),
                                  ('7AP', '7ème Année Fondamentale'),
                                  ('8AP', '8ème Année Fondamentale'),
                                  ('9AP', '9ème Année Fondamentale'),
                                  ('1AS', '1ère Année Secondaire'),
                                  ('2AS', '2ème Année Secondaire'),
                                  ('TL', 'Terminale L'),
                                  ('TS', 'Terminale S'),
                                  ('TC', 'Terminale C'),
                                  # ... autres niveaux si nécessaire
                              ])
    serie = models.CharField(max_length=50, blank=True, null=True, verbose_name="Série (pour le Secondaire)")
    enseignant_principal = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='classes_principales', verbose_name="Enseignant Principal")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année Scolaire")

    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        unique_together = ('nom_classe', 'annee_scolaire') # Une classe avec le même nom ne peut exister qu'une fois par an
        ordering = ['annee_scolaire', 'niveau', 'nom_classe']

    def __str__(self):
        return f"{self.nom_classe} ({self.annee_scolaire.annee})"

# Modèle pour les matières
class Matiere(models.Model):
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
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, verbose_name="Classe")
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, verbose_name="Matière")
    enseignant = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Enseignant de la matière")
    coefficient = models.IntegerField(default=1, verbose_name="Coefficient")

    class Meta:
        verbose_name = "Programme Matière par Classe"
        verbose_name_plural = "Programmes Matières par Classe"
        unique_together = ('classe', 'matiere') # Une matière n'a qu'un seul coefficient par classe
        ordering = ['classe', 'matiere__nom']

    def __str__(self):
        return f"{self.matiere.nom} ({self.coefficient}) en {self.classe.nom_classe}"


# Modèle pour les étudiants/élèves
class Etudiant(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]

    SITUATION_CHOICES = [
        ('Actif', 'Actif'),
        ('Ancien', 'Ancien'),
        ('Suspendu', 'Suspendu'),
        ('Radié', 'Radié'),
    ]

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
    # Chaque étudiant est inscrit à une classe pour une année scolaire donnée
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
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='dossier_images', verbose_name="Élève")
    image = models.ImageField(upload_to='dossiers_inscription/', verbose_name="Fichier (Image ou PDF)") # Peut être adapté pour PDF si besoin
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Description du document")
    date_telechargement = models.DateTimeField(auto_now_add=True, verbose_name="Date de Téléchargement")

    class Meta:
        verbose_name = "Document d'Inscription"
        verbose_name_plural = "Documents d'Inscription"
        ordering = ['etudiant', 'description']

    def __str__(self):
        return f"Dossier de {self.etudiant} - {self.description or 'Document'}"


# Modèle pour les notes des élèves
class Note(models.Model):
    PERIODE_EVALUATION_CHOICES = [
        ('Trimestre 1', 'Trimestre 1'),
        ('Trimestre 2', 'Trimestre 2'),
        ('Trimestre 3', 'Trimestre 3'),
        ('Annuelle', 'Annuelle'), # Pour la moyenne annuelle
    ]

    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, verbose_name="Élève")
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, verbose_name="Matière")
    valeur = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Note Obtenue (sur 20)") # Ex: 15.50
    periode_evaluation = models.CharField(max_length=20, choices=PERIODE_EVALUATION_CHOICES, verbose_name="Période d'Évaluation")
    type_evaluation = models.CharField(max_length=50, blank=True, null=True, verbose_name="Type d'Évaluation (Devoir, Composition, etc.)")
    date_evaluation = models.DateField(default=timezone.now, verbose_name="Date de l'Évaluation")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année Scolaire")

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        # Empêche d'avoir plusieurs notes pour le même élève, la même matière, la même période et la même année
        unique_together = ('etudiant', 'matiere', 'periode_evaluation', 'annee_scolaire')
        ordering = ['annee_scolaire', 'etudiant', 'periode_evaluation', 'matiere__nom']

    def __str__(self):
        return f"{self.etudiant.prenom} {self.etudiant.nom} - {self.matiere.nom} ({self.periode_evaluation}): {self.valeur}/20"

    def get_coefficient(self):
        """Récupère le coefficient de la matière pour la classe de l'étudiant."""
        try:
            return ProgrammeMatiere.objects.get(classe=self.etudiant.classe, matiere=self.matiere).coefficient
        except ProgrammeMatiere.DoesNotExist:
            return 1 # Coefficient par défaut si non trouvé


# Modèle pour le suivi des paiements
class Paiement(models.Model):
    STATUT_PAIEMENT_CHOICES = [
        ('Payé', 'Payé'),
        ('Impayé', 'Impayé'),
        ('Partiel', 'Partiel'),
    ]

    MOTIF_PAIEMENT_CHOICES = [
        ('Frais de Scolarité', 'Frais de Scolarité'),
        ('Frais d\'Inscription', 'Frais d\'Inscription'),
        ('Cotisation APEM', 'Cotisation APEM'),
        ('Tenue Scolaire', 'Tenue Scolaire'),
        ('Repas Scolaire', 'Repas Scolaire'),
        ('Autres', 'Autres'),
    ]

    MODE_PAIEMENT_CHOICES = [
        ('Espèces', 'Espèces'),
        ('Chèque', 'Chèque'),
        ('Virement Bancaire', 'Virement Bancaire'),
        ('Mobile Money', 'Mobile Money'), # Très pertinent au Mali
    ]

    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, verbose_name="Élève")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant Payé (XOF)")
    montant_du = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant Total Dû", blank=True, null=True) # Utile pour le solde
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
        return f"Paiement de {self.etudiant.prenom} {self.etudiant.nom} - {self.montant} XOF ({self.statut})"

# Modèle pour le suivi des présences
class Presence(models.Model):
    STATUT_PRESENCE_CHOICES = [
        ('Présent', 'Présent'),
        ('Absent', 'Absent'),
        ('Retard', 'Retard'),
        ('Excusé', 'Excusé'), # Absent justifié
    ]

    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, verbose_name="Élève")
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
        # Un élève ne peut avoir qu'un seul statut de présence pour une matière donnée à une date donnée
        # Ou, si la présence est journalière pour toute la journée: unique_together = ('etudiant', 'date', 'annee_scolaire')
        unique_together = ('etudiant', 'date', 'matiere', 'annee_scolaire')
        ordering = ['-date', 'classe__nom_classe', 'etudiant__nom']

    def __str__(self):
        return f"{self.etudiant.prenom} {self.etudiant.nom} - {self.date} ({self.statut})"

# Modèle pour les certificats de fréquentation (pour garder une trace des certificats générés)
class CertificatFrequentation(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, verbose_name="Élève")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année Scolaire")
    date_delivrance = models.DateField(default=timezone.now, verbose_name="Date de Délivrance")
    numero_certificat = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Numéro du Certificat")
    fichier_pdf = models.FileField(upload_to='certificats_frequentation/', blank=True, null=True, verbose_name="Fichier PDF du Certificat")
    delivre_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Délivré par")

    class Meta:
        verbose_name = "Certificat de Fréquentation"
        verbose_name_plural = "Certificats de Fréquentation"
        unique_together = ('etudiant', 'annee_scolaire') # Un seul certificat par an et par élève
        ordering = ['-annee_scolaire', 'etudiant__nom']

    def __str__(self):
        return f"Certificat de {self.etudiant} pour {self.annee_scolaire}"


    