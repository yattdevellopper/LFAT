# dashboard/forms.py
from django import forms
from .models import Etudiant, Classe, AnneeScolaire, Enseignant, Matiere, Note, Paiement, Presence, DossierInscriptionImage, CertificatFrequentation, ProgrammeMatiere
from datetime import datetime
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
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
        }

    # Vous pouvez ajouter un __init__ pour filtrer les classes par année scolaire active si besoin
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supposons que nous voulons afficher seulement les classes de l'année scolaire active pour l'inscription
        try:
            annee_active = AnneeScolaire.objects.get(active=True)
            self.fields['classe'].queryset = Classe.objects.filter(annee_scolaire=annee_active)
            self.fields['annee_scolaire_inscription'].initial = annee_active
            self.fields['annee_scolaire_inscription'].queryset = AnneeScolaire.objects.all() # Permet de choisir une année historique
        except AnneeScolaire.DoesNotExist:
            pass # Gérer le cas où aucune année active n'est définie


# Formulaire pour les images du dossier d'inscription (pour upload multiple, nécessitera un peu plus de logique côté vue)
class DossierInscriptionImageForm(forms.ModelForm):
    class Meta:
        model = DossierInscriptionImage
        fields = ['image', 'description']

# Formulaire pour les Notes
class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['etudiant', 'matiere', 'valeur', 'periode_evaluation', 'type_evaluation', 'date_evaluation', 'annee_scolaire']
        widgets = {
            'date_evaluation': forms.DateInput(attrs={'type': 'date'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            annee_active = AnneeScolaire.objects.get(active=True)
            self.fields['annee_scolaire'].initial = annee_active
            self.fields['annee_scolaire'].queryset = AnneeScolaire.objects.all()
        except AnneeScolaire.DoesNotExist:
            pass

# Formulaire pour les Paiements
class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ['etudiant', 'montant', 'montant_du', 'date_paiement', 'motif_paiement', 'statut', 'mode_paiement', 'recu_numero', 'annee_scolaire']
        widgets = {
            'date_paiement': forms.DateInput(attrs={'type': 'date'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            annee_active = AnneeScolaire.objects.get(active=True)
            self.fields['annee_scolaire'].initial = annee_active
            self.fields['annee_scolaire'].queryset = AnneeScolaire.objects.all()
        except AnneeScolaire.DoesNotExist:
            pass

# Formulaire pour les Présences
class PresenceForm(forms.ModelForm):
    est_present = forms.BooleanField(
        required=False,
        label="Présent",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # --- THIS IS THE CRITICAL CHANGE ---
    statut_detail = forms.ChoiceField(
        choices=Presence.STATUT_PRESENCE_CHOICES[1:], # Use STATUT_PRESENCE_CHOICES
        required=False,
        label="Statut Détail",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    # -----------------------------------
    
    etudiant = forms.ModelChoiceField(queryset=Etudiant.objects.all(), widget=forms.HiddenInput(), required=False)
    classe = forms.ModelChoiceField(queryset=Classe.objects.all(), widget=forms.HiddenInput(), required=False)
    date = forms.DateField(widget=forms.HiddenInput(), required=False)
    annee_scolaire = forms.ModelChoiceField(queryset=AnneeScolaire.objects.all(), widget=forms.HiddenInput(), required=False)
    statut = forms.CharField(widget=forms.HiddenInput(), required=False) # Field updated by JS

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
        # Ensure hidden fields don't get auto-labels from crispy-forms
        self.fields['etudiant'].label = ''
        self.fields['classe'].label = ''
        self.fields['date'].label = ''
        self.fields['annee_scolaire'].label = ''
        self.fields['statut'].label = ''
        
        # Ensure the queryset for 'matiere' is properly defined
        if 'matiere' in self.fields:
            self.fields['matiere'].queryset = Matiere.objects.all() # Assuming Matiere is imported and exists

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Assurez-vous que les champs HiddenInput ne sont pas rendus avec des labels automatiques par crispy-forms
        self.fields['etudiant'].label = ''
        self.fields['classe'].label = ''
        self.fields['date'].label = ''
        self.fields['annee_scolaire'].label = ''
        self.fields['statut'].label = ''

        # S'assurer que le queryset pour 'matiere' est bien défini si c'est un ModelChoiceField
        if 'matiere' in self.fields:
            self.fields['matiere'].queryset = Matiere.objects.all() # Assurez-vous que Matiere est importé et existe
# Formulaire pour les Enseignants
class EnseignantForm(forms.ModelForm):
    class Meta:
        model = Enseignant
        fields = ['nom', 'prenom', 'contact', 'email', 'specialite']

# Formulaire pour les Matières
class MatiereForm(forms.ModelForm):
    class Meta:
        model = Matiere
        fields = ['nom', 'code_matiere']

# Formulaire pour les Classes
class ClasseForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['nom_classe', 'niveau', 'serie', 'enseignant_principal', 'annee_scolaire']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            annee_active = AnneeScolaire.objects.get(active=True)
            self.fields['annee_scolaire'].initial = annee_active
            self.fields['annee_scolaire'].queryset = AnneeScolaire.objects.all()
        except AnneeScolaire.DoesNotExist:
            pass

# Formulaire pour ProgrammeMatiere (utile pour ajouter les coefficients)
class ProgrammeMatiereForm(forms.ModelForm):
    class Meta:
        model = ProgrammeMatiere
        fields = ['classe', 'matiere', 'enseignant', 'coefficient']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            annee_active = AnneeScolaire.objects.get(active=True)
            # Filter classes to show only for the active year
            self.fields['classe'].queryset = Classe.objects.filter(annee_scolaire=annee_active)
        except AnneeScolaire.DoesNotExist:
            pass

# Formulaire pour AnneeScolaire

class AnneeScolaireForm(forms.ModelForm):
    class Meta:
        model = AnneeScolaire
        fields = ['annee', 'active']
        
        widgets = {
            'annee': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2023-2024'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'annee': 'Année Scolaire',
            'active': 'Année Active',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si le formulaire n'est PAS lié à une instance existante (c'est-à-dire pour la création)
        if not self.instance.pk:
            current_year = datetime.now().year
            # Si le mois actuel est après juillet (disons à partir d'août), l'année scolaire commence par l'année actuelle
            # Sinon, elle a commencé l'année précédente
            # Vous pouvez ajuster le mois de début d'année scolaire (ici, 8 pour août)
            if datetime.now().month >= 8: # Par exemple, si l'année scolaire commence en août
                next_year = current_year + 1
            else: # Sinon, l'année scolaire a commencé l'année précédente
                next_year = current_year
                current_year = current_year - 1

            self.fields['annee'].initial = f"{current_year}-{next_year}"