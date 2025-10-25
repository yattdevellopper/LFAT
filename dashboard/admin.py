# dashboard/admin.py
from django.contrib import admin
from .models import (
    AnneeScolaire, Enseignant, Classe, Matiere, ProgrammeMatiere,
    Etudiant, DossierInscriptionImage, Note, Paiement, Presence,
    CertificatFrequentation, EcoleSettings , EmploiDuTemps , Profile
)


admin.site.register(EcoleSettings)
admin.site.register(Profile)


@admin.register(EmploiDuTemps)
class EmploiDuTempsAdmin(admin.ModelAdmin):
    list_display = ('classe', 'jour', 'heure_debut', 'heure_fin', 'matiere', 'enseignant', 'annee_scolaire')
    list_filter = ('classe', 'jour', 'enseignant', 'matiere', 'annee_scolaire')
    search_fields = ('classe__nom_classe', 'enseignant__nom', 'matiere__nom')

admin.site.register(AnneeScolaire)
admin.site.register(Enseignant)
admin.site.register(Classe)
admin.site.register(Matiere)
admin.site.register(ProgrammeMatiere)
admin.site.register(Etudiant)
admin.site.register(DossierInscriptionImage)
admin.site.register(Note)
admin.site.register(Paiement)
admin.site.register(Presence)
admin.site.register(CertificatFrequentation)