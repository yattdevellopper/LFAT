# dashboard/admin.py
from django.contrib import admin
from .models import (
    AnneeScolaire, Enseignant, Classe, Matiere, ProgrammeMatiere,
    Etudiant, DossierInscriptionImage, Note, Paiement, Presence,
    CertificatFrequentation
)

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