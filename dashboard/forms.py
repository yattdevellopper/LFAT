from django import forms
from .models import (
    EcoleSettings, EmploiDuTemps, Etudiant, Classe, AnneeScolaire, Enseignant, Matiere, Note, Paiement,
    Presence, DossierInscriptionImage, CertificatFrequentation, ProgrammeMatiere
)
from django.utils import timezone

from django.db.models import ObjectDoesNotExist # Importation utile pour la gestion d'erreurs

# ====================================================================
# Fonctions utilitaires
# ====================================================================

def get_active_annee_scolaire():
    """Tente de récupérer l'année scolaire active."""
    try:
        return AnneeScolaire.objects.get(active=True)
    except ObjectDoesNotExist:
        return None

# ====================================================================
# FORMULAIRES PRINCIPAUX
# ====================================================================

# Formulaire pour l'élève
class EtudiantForm(forms.ModelForm):
    class Meta:
        model = Etudiant
        fields = [
            'nom', 'prenom', 'date_naissance', 'lieu_naissance', 'genre',
            'nationalite', 'adresse', 'ville', 'contact_parent', 'email_parent',
            'numero_matricule', 'classe', 'annee_scolaire_inscription',
            'photo_profil', 'statut'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'genre': forms.Select(attrs={'class': 'form-select'}),
            'nationalite': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_parent': forms.TextInput(attrs={'class': 'form-control'}),
            'email_parent': forms.EmailInput(attrs={'class': 'form-control'}),
            'numero_matricule': forms.TextInput(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-select'}),
            'annee_scolaire_inscription': forms.Select(attrs={'class': 'form-select'}),
            'photo_profil': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.ecole = kwargs.pop('ecole', None)
        super().__init__(*args, **kwargs)

        if not self.ecole:
            raise ValueError("Une école doit être fournie pour filtrer les classes et années scolaires.")

        # 🔹 Année scolaire active pour la pré-sélection
        annee_active = AnneeScolaire.objects.filter(active=True, ecole=self.ecole).first()

        # 🔹 Filtrer les classes de l'école
        if annee_active:
            self.fields['classe'].queryset = Classe.objects.filter(ecole=self.ecole).order_by('nom_classe')
        else:
            self.fields['classe'].queryset = Classe.objects.filter(ecole=self.ecole).order_by('nom_classe')

        # 🔹 Pré-remplir l'année scolaire uniquement à la création
        if not self.instance.pk and annee_active:
            self.fields['annee_scolaire_inscription'].initial = annee_active

        # 🔹 Filtrer les années scolaires pour l'école
        self.fields['annee_scolaire_inscription'].queryset = AnneeScolaire.objects.filter(ecole=self.ecole).order_by('-annee')




# Formulaire pour les images du dossier d'inscription
class DossierInscriptionImageForm(forms.ModelForm):
    class Meta:
        model = DossierInscriptionImage
        fields = ['image', 'description']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Formulaire pour les Notes
class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['matiere', 'valeur', 'periode_evaluation', 'type_evaluation', 'date_evaluation', 'annee_scolaire']
        widgets = {
            'matiere': forms.Select(attrs={'class': 'form-select'}),
            'periode_evaluation': forms.Select(attrs={'class': 'form-select'}),
            'type_evaluation': forms.TextInput(attrs={'class': 'form-control'}),
            'valeur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '20'}),
            'date_evaluation': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'annee_scolaire': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'profile') and user.profile.ecole:
            ecole = user.profile.ecole

            # Filtrer les matières par école
            self.fields['matiere'].queryset = Matiere.objects.filter(ecole=ecole).order_by('nom')

            # Pré-remplir l'année scolaire active
            annee_active = AnneeScolaire.objects.filter(active=True, ecole=ecole).first()
            if annee_active:
                self.fields['annee_scolaire'].initial = annee_active.pk
                self.fields['annee_scolaire'].queryset = AnneeScolaire.objects.filter(ecole=ecole)

class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = [
            'etudiant', 'montant', 'montant_du', 'date_paiement', 
            'motif_paiement', 'statut', 'mode_paiement', 
            'recu_numero', 'annee_scolaire'
        ]
        widgets = {
            'date_paiement': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'etudiant': forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'montant_du': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'motif_paiement': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}),
            'recu_numero': forms.TextInput(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        # On peut passer l'école depuis la vue
        self.ecole = kwargs.pop('ecole', None)
        super().__init__(*args, **kwargs)

        # Filtrer les étudiants selon l'école
        if self.ecole:
            self.fields['etudiant'].queryset = Etudiant.objects.filter(ecole=self.ecole)
            # Limiter les années scolaires à celles de l'école
            self.fields['annee_scolaire'].queryset = AnneeScolaire.objects.filter(ecole=self.ecole)
        else:
            # fallback
            self.fields['etudiant'].queryset = Etudiant.objects.all()
            self.fields['annee_scolaire'].queryset = AnneeScolaire.objects.all()

        # Pré-remplir l'année scolaire active si elle existe
        if self.ecole:
            annee_active = AnneeScolaire.objects.filter(active=True, ecole=self.ecole).first()
            if annee_active and not self.instance.pk:
                self.fields['annee_scolaire'].initial = annee_active



# Formulaire pour les Présences (Conçu pour être utilisé dans un formulaire dynamique par élève)
class PresenceForm(forms.ModelForm):
    # Champ booléen pour indiquer la présence rapide
    est_present = forms.BooleanField(
        required=False,
        label="Présent",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input presence-checkbox'})
    )
    
    # Champ pour choisir le statut détaillé si non présent (Absent, Retard, Excusé)
    # Exclut le statut 'Présent' du choix
    statut_detail = forms.ChoiceField(
        choices=[(c[0], c[1]) for c in Presence.STATUT_PRESENCE_CHOICES if c[0] != 'Présent'],
        required=False,
        label="Statut (Si absent)",
        widget=forms.Select(attrs={'class': 'form-select statut-detail-select'})
    )
    
    # Champs HiddenInput qui seront fixés par la vue (ou JS)
    etudiant = forms.ModelChoiceField(queryset=Etudiant.objects.all(), widget=forms.HiddenInput(), required=False)
    classe = forms.ModelChoiceField(queryset=Classe.objects.all(), widget=forms.HiddenInput(), required=False)
    date = forms.DateField(widget=forms.HiddenInput(), required=False)
    annee_scolaire = forms.ModelChoiceField(queryset=AnneeScolaire.objects.all(), widget=forms.HiddenInput(), required=False)
    statut = forms.CharField(widget=forms.HiddenInput(), required=False) # Champ qui recevra la valeur finale ('Présent', 'Absent', etc.)

    class Meta:
        model = Presence
        fields = [
            'est_present', 'statut_detail', 'matiere', 'heure_debut_cours',
            'heure_fin_cours', 'motif_absence_retard', 'justificatif_fourni',
            'etudiant', 'classe', 'date', 'annee_scolaire', 'statut'
        ]
        widgets = {
            'heure_debut_cours': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'heure_fin_cours': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'motif_absence_retard': forms.TextInput(attrs={'class': 'form-control'}),
            'justificatif_fourni': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'matiere': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cacher les labels des champs HiddenInput
        for field_name in ['etudiant', 'classe', 'date', 'annee_scolaire', 'statut']:
            if field_name in self.fields:
                self.fields[field_name].label = ''
        
        # S'assurer que le queryset pour 'matiere' est bien défini
        if 'matiere' in self.fields:
            self.fields['matiere'].queryset = Matiere.objects.all()


# Formulaire pour les Enseignants
class EnseignantForm(forms.ModelForm):
    class Meta:
        model = Enseignant
        fields = ['nom', 'prenom', 'contact', 'email', 'specialite']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'specialite': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Formulaire pour les Matières
class MatiereForm(forms.ModelForm):
    class Meta:
        model = Matiere
        fields = ['nom', 'code_matiere']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'code_matiere': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Formulaire pour les Classes


class ClasseForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['nom_classe', 'niveau', 'serie', 'enseignant_principal', 'annee_scolaire']
        widgets = {
            'nom_classe': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau': forms.Select(attrs={'class': 'form-select'}),
            'serie': forms.TextInput(attrs={'class': 'form-control'}),
            'enseignant_principal': forms.Select(attrs={'class': 'form-select'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        # On peut passer l'école depuis la vue
        self.ecole = kwargs.pop('ecole', None)
        super().__init__(*args, **kwargs)

        # Filtrage des enseignants par école si fourni
        if self.ecole:
            self.fields['enseignant_principal'].queryset = Enseignant.objects.filter(ecole=self.ecole)
        else:
            self.fields['enseignant_principal'].queryset = Enseignant.objects.all()

        # Récupération de l'année scolaire active
        annee_active = None
        if self.ecole:
            # ⚠️ filter(...).first() pour éviter MultipleObjectsReturned
            annee_active = AnneeScolaire.objects.filter(ecole=self.ecole, active=True).first()

        if annee_active and not self.instance.pk:
            # Pré-remplissage de l'année active par défaut pour la création
            self.fields['annee_scolaire'].initial = annee_active

        # Filtrer les années scolaires disponibles par école
        if self.ecole:
            self.fields['annee_scolaire'].queryset = AnneeScolaire.objects.filter(ecole=self.ecole).order_by('-annee')
        else:
            self.fields['annee_scolaire'].queryset = AnneeScolaire.objects.all().order_by('-annee')

        # Désactiver le champ année_scolaire si on modifie une classe existante
        if self.instance.pk:
            self.fields['annee_scolaire'].disabled = True


# Formulaire pour ProgrammeMatiere (lier matière à classe avec coefficient)
class ProgrammeMatiereForm(forms.ModelForm):
    class Meta:
        model = ProgrammeMatiere
        fields = ['classe', 'matiere', 'enseignant', 'coefficient']  # pas 'annee_scolaire'
        widgets = {
            'classe': forms.Select(attrs={'class': 'form-select'}),
            'matiere': forms.Select(attrs={'class': 'form-select'}),
            'enseignant': forms.Select(attrs={'class': 'form-select'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }

    def __init__(self, *args, **kwargs):
        self.ecole = kwargs.pop('ecole', None)
        super().__init__(*args, **kwargs)

        # Récupérer l'année scolaire active pour filtrer les classes
        if self.ecole:
            annee_active = AnneeScolaire.objects.filter(active=True, ecole=self.ecole).first()
            if annee_active:
                self.fields['classe'].queryset = Classe.objects.filter(
                    annee_scolaire=annee_active,
                    ecole=self.ecole
                )
            self.fields['matiere'].queryset = Matiere.objects.filter(ecole=self.ecole)
            self.fields['enseignant'].queryset = Enseignant.objects.filter(ecole=self.ecole)




class AnneeScolaireForm(forms.ModelForm):
    class Meta:
        model = AnneeScolaire
        fields = ['annee', 'date_debut', 'date_fin', 'active']
        widgets = {
            'annee': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 2023-2024'
            }),
            'date_debut': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'date_fin': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'annee': 'Année Scolaire',
            'active': 'Année Active (en cours)',
        }

    def __init__(self, *args, **kwargs):
        # Récupérer l'école depuis la vue
        self.ecole = kwargs.pop('ecole', None)
        super().__init__(*args, **kwargs)

        # Pré-remplissage automatique à la création
        if not self.instance.pk:
            today = timezone.now().date()
            start_year = today.year if today.month >= 8 else today.year - 1
            end_year = start_year + 1
            self.fields['annee'].initial = f"{start_year}-{end_year}"

        # Désactiver l'édition du champ année lors de la modification
        if self.instance.pk:
            self.fields['annee'].disabled = True

    def clean_annee(self):
        """Vérifie que l'année scolaire est unique pour l'école"""
        annee = self.cleaned_data['annee']
        ecole = self.ecole or getattr(self.instance, 'ecole', None)

        if ecole:
            qs = AnneeScolaire.objects.filter(annee=annee, ecole=ecole)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)  # Exclure l'instance actuelle
            if qs.exists():
                raise forms.ValidationError(
                    "Cette année scolaire existe déjà pour votre école."
                )
        return annee



class CertificatFrequentationForm(forms.ModelForm):
    class Meta:
        model = CertificatFrequentation
        fields = [
            'etudiant',
            'annee_scolaire',
            'date_delivrance',
            'lieu_delivrance',
            'numero_certificat',
            'fichier_pdf',
            'cachet_utilise',
            'signature_utilisee',
            'ministere',
            'academie',
            'etablissement_reference',
            'adresse_etablissement',
            'mention_legale',
            'qr_code',
            'code_verification',
            'statut',
            'remarque',
        ]

        widgets = {
            'etudiant': forms.Select(attrs={'class': 'form-select'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-select'}),
            'date_delivrance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'lieu_delivrance': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Bamako'}),
            'numero_certificat': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CERT-2025-0001'}),
            'fichier_pdf': forms.FileInput(attrs={'class': 'form-control'}),
            'ministere': forms.TextInput(attrs={'class': 'form-control'}),
            'academie': forms.TextInput(attrs={'class': 'form-control'}),
            'etablissement_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse_etablissement': forms.TextInput(attrs={'class': 'form-control'}),
            'mention_legale': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': 'Ce certificat est délivré sous la responsabilité du Directeur...'
            }),
            'cachet_utilise': forms.HiddenInput(),
            'signature_utilisee': forms.HiddenInput(),
            'qr_code': forms.HiddenInput(),
            'code_verification': forms.HiddenInput(),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'remarque': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        initial_data = kwargs.get('initial', {})
        super().__init__(*args, **kwargs)

        # 🔹 Vérifier si l'utilisateur est lié à une école
        ecole = getattr(getattr(user, 'profile', None), 'ecole', None) if user and user.is_authenticated else None

        if ecole:
            # 🔹 Filtrer les élèves de cette école
            self.fields['etudiant'].queryset = Etudiant.objects.filter(ecole=ecole).order_by('nom', 'prenom')

            # 🔹 Filtrer les années scolaires actives
            self.fields['annee_scolaire'].queryset = AnneeScolaire.objects.filter(active=True, ecole=ecole)

            # 🔹 Pré-remplir l'année active
            annee_active = AnneeScolaire.objects.filter(active=True, ecole=ecole).first()
            if annee_active and 'annee_scolaire' not in initial_data:
                self.fields['annee_scolaire'].initial = annee_active
        else:
            self.fields['etudiant'].queryset = Etudiant.objects.none()
            self.fields['annee_scolaire'].queryset = AnneeScolaire.objects.none()

        # 🔹 Pré-remplir l’élève si présent
        if 'etudiant' in initial_data:
            self.fields['etudiant'].initial = initial_data['etudiant']

        # 🔹 Pré-remplir la date de délivrance
        if 'date_delivrance' not in initial_data:
            self.fields['date_delivrance'].initial = timezone.now().date()

        # 🔹 Donner un texte par défaut à la mention légale
        if not self.fields['mention_legale'].initial:
            self.fields['mention_legale'].initial = (
                "Ce certificat est délivré sous la responsabilité du Directeur et ne peut être reproduit sans autorisation."
            )

        # 🔹 Masquer les labels inutiles
        for champ in ['cachet_utilise', 'signature_utilisee', 'qr_code', 'code_verification']:
            self.fields[champ].label = ''

class EmploiDuTempsForm(forms.ModelForm):
    class Meta:
        model = EmploiDuTemps
        fields = ['classe', 'matiere', 'enseignant', 'jour', 'heure_debut', 'heure_fin']

        widgets = {
            'classe': forms.Select(attrs={'class': 'form-select'}),
            'matiere': forms.Select(attrs={'class': 'form-select'}),
            'enseignant': forms.Select(attrs={'class': 'form-select'}),
            'jour': forms.Select(attrs={'class': 'form-select'}),
            'heure_debut': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        # 🔹 Récupération de l'école passée en argument
        ecole = kwargs.pop('ecole', None)
        super().__init__(*args, **kwargs)

        if ecole:
            # Filtrer les classes, matières et enseignants selon l'école
            self.fields['classe'].queryset = Classe.objects.filter(ecole=ecole)
            self.fields['matiere'].queryset = Matiere.objects.filter(ecole=ecole)
            self.fields['enseignant'].queryset = Enseignant.objects.filter(ecole=ecole)


class EcoleSettingsForm(forms.ModelForm):
    """
    Formulaire de gestion complète des paramètres d'établissement.
    Compatible avec les vues Admin et personnalisées.
    """
    class Meta:
        model = EcoleSettings
        fields = [
            'ministere',
            'academie',
            'commune',
            'nom_etablissement',
            'adresse_etablissement',
            'telephone',
            'email_contact',
            'site_web',
            'code_etablissement',
            'logo',
            'cachet_admin',
            'signature_directeur',
            'titre_signataire',
            'nom_signataire',
        ]

        # Définition des widgets uniformes
        widgets = {
            'ministere': forms.TextInput(attrs={'class': 'form-control'}),
            'academie': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_etablissement': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse_etablissement': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email_contact': forms.EmailInput(attrs={'class': 'form-control'}),
            'site_web': forms.URLInput(attrs={'class': 'form-control'}),
            'code_etablissement': forms.TextInput(attrs={'class': 'form-control'}),
            'titre_signataire': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_signataire': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'cachet_admin': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'signature_directeur': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        """
        Validation stricte pour garantir :
        - Une seule instance EcoleSettings dans la base
        - Poids maximum des fichiers images
        """
        cleaned_data = super().clean()

        # Empêche plusieurs configurations
        if EcoleSettings.objects.exclude(id=self.instance.id).exists():
            # Attention : cette validation pourrait être mieux gérée par un SingletonModel,
            # mais elle est maintenue ici pour la compatibilité avec le code existant.
            raise ValidationError("Il ne peut y avoir qu'une seule configuration d'école.")

        # Vérifie la taille maximale des fichiers image
        max_size = 3 * 1024 * 1024  # 3 Mo
        for champ in ['logo', 'cachet_admin', 'signature_directeur']:
            fichier = cleaned_data.get(champ)
            if fichier and hasattr(fichier, 'size') and fichier.size > max_size:
                raise ValidationError(
                    f"Le fichier '{champ}' dépasse la taille maximale autorisée (3 Mo)."
                )

        return cleaned_data