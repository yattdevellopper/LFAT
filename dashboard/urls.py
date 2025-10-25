# dashboard/urls.py
from django.urls import path
from . import views



# app_name = "settings"

urlpatterns = [
    path('recherche-globale/', views.recherche_etudiants, name='recherche_etudiants_globale'),
    path('paiement-initier/', views.initier_paiement, name='initier_paiement'),

    # Dashboard général
    path('', views.dashboard_accueil, name='dashboard_accueil'),

    path('config/', views.config_ecole_view, name='ecole_settings'),

    # CRUD Années Scolaires
    path('annees-scolaires/', views.liste_annees_scolaires, name='liste_annees_scolaires'),
    path('annees-scolaires/creer/', views.creer_annee_scolaire, name='creer_annee_scolaire'),
    path('annees-scolaires/modifier/<int:pk>/', views.modifier_annee_scolaire, name='modifier_annee_scolaire'),
    path('annees-scolaires/supprimer/<int:pk>/', views.supprimer_annee_scolaire, name='supprimer_annee_scolaire'),

    # CRUD Étudiants
    path('etudiants/', views.liste_etudiants, name='liste_etudiants'),
    path('etudiants/creer/', views.creer_etudiant, name='creer_etudiant'),
    path('etudiants/<int:etudiant_id>/', views.detail_etudiant, name='detail_etudiant'),
    path('etudiants/<int:etudiant_id>/modifier/', views.modifier_etudiant, name='modifier_etudiant'),
    path('etudiants/<int:etudiant_id>/supprimer/', views.supprimer_etudiant, name='supprimer_etudiant'),

    # Notes (liées à l'étudiant)
    path('etudiants/<int:etudiant_id>/ajouter-note/', views.ajouter_note, name='ajouter_note'),
    path('notes/modifier/<int:pk>/', views.modifier_note, name='modifier_note'),
    path('notes/supprimer/<int:pk>/', views.supprimer_note, name='supprimer_note'),

    # Paiements (liés à l'étudiant)
    path('etudiants/<int:etudiant_id>/ajouter-paiement/', views.ajouter_paiement, name='ajouter_paiement'),
    path('paiements/modifier/<int:pk>/', views.modifier_paiement, name='modifier_paiement'),
    path('paiements/supprimer/<int:pk>/', views.supprimer_paiement, name='supprimer_paiement'),
    path('paiements/payes/', views.liste_paiements_payes, name='liste_paiements_payes'),
    path('paiements/par_classe_etudiant/', views.liste_paiements_par_classe_etudiant, name='liste_paiements_par_classe_etudiant'),
    path('paiement/<int:paiement_id>/recu/', views.generer_recu_paiement, name='generer_recu_paiement'),



    
    # Présences
    path('presences/classe/<int:classe_id>/marquer/', views.marquer_presence_classe, name='marquer_presence_classe'),
    path('presences/classe/<int:classe_id>/suivi/', views.suivi_presence_classe, name='suivi_presence_classe'),
    path('presences/eleve/<int:etudiant_id>/suivi/', views.suivi_presence_eleve, name='suivi_presence_eleve'),
    path('presences/', views.liste_presences, name='liste_presences'),


    # Certificats de fréquentation
    path('etudiants/<int:etudiant_id>/generer-certificat/', views.generer_certificat_frequentation, name='generer_certificat_frequentation'),

    # Génération de bulletins scolaires
    path('etudiants/<int:etudiant_id>/generer-bulletin/<str:periode>/', views.generer_bulletin_scolaire, name='generer_bulletin_scolaire'),

    # CRUD Classes
    path('classes/', views.liste_classes, name='liste_classes'),
    path('classes/creer/', views.creer_classe, name='creer_classe'),
    path('classes/modifier/<int:pk>/', views.modifier_classe, name='modifier_classe'),
    path('classes/supprimer/<int:pk>/', views.supprimer_classe, name='supprimer_classe'),

    # CRUD Matières
    path('matieres/', views.liste_matieres, name='liste_matieres'),
    path('matieres/creer/', views.creer_matiere, name='creer_matiere'),
    path('matieres/modifier/<int:pk>/', views.modifier_matiere, name='modifier_matiere'),
    path('matieres/supprimer/<int:pk>/', views.supprimer_matiere, name='supprimer_matiere'),

    # CRUD Enseignants
    path('enseignants/', views.liste_enseignants, name='liste_enseignants'),
    path('enseignants/creer/', views.creer_enseignant, name='creer_enseignant'),
    path('enseignants/modifier/<int:pk>/', views.modifier_enseignant, name='modifier_enseignant'),
    path('enseignants/supprimer/<int:pk>/', views.supprimer_enseignant, name='supprimer_enseignant'),

    # CRUD Programme Matière
    path('programmes-matiere/', views.liste_programmes_matiere, name='liste_programmes_matiere'),
    path('programmes-matiere/creer/', views.creer_programme_matiere, name='creer_programme_matiere'),
    path('programmes-matiere/modifier/<int:pk>/', views.modifier_programme_matiere, name='modifier_programme_matiere'),
    path('programmes-matiere/supprimer/<int:pk>/', views.supprimer_programme_matiere, name='supprimer_programme_matiere'),

    path('emplois-du-temps/', views.liste_emplois_du_temps, name='liste_emplois_du_temps'),
    path('emplois-du-temps/creer/', views.creer_emploi_du_temps, name='creer_emploi_du_temps'),
    path('emplois-du-temps/<int:classe_id>/creer/', views.creer_emploi_du_temps_pour_classe, name='creer_emploi_du_temps_pour_classe'),
    path('emplois-du-temps/<int:classe_id>/modifier/', views.modifier_emploi_du_temps_classe, name='modifier_emploi_du_temps_classe'),
    path('emplois-du-temps/bloc/<int:pk>/modifier/', views.modifier_emploi_du_temps, name='modifier_emploi_du_temps'),

    # generer bulletin scolaire

    path('notes/export/<str:periode>/', views.export_notes_excel, name='export_notes_excel'),
    path('notes/import/', views.import_notes_excel, name='import_notes_excel'),
    path('etudiant/<int:etudiant_id>/bulletin/<str:periode>/pdf/', views.generer_bulletin_scolaire, name='generer_bulletin_scolaire'),
    path('notes/gestion/', views.liste_notes_par_classe, name='liste_notes_par_classe_matiere'),

    
    # Chemin pour la saisie et modification des notes en bloc
    # Nécessite l'ID de la classe et de la matière dans l'URL
    path( 'notes/liste/<int:classe_id>/<int:matiere_id>/',   views.liste_notes_par_classe, name='liste_notes_par_classe_matiere'  ),    
    # Chemin pour modifier une seule note (par clé primaire)
    path("notes/modifier/<int:pk>/", views.modifier_note, name="modifier_note"),

    # Chemin pour supprimer une seule note (par clé primaire)
    path('notes/supprimer/<int:note_pk>/', views.supprimer_note, name='supprimer_note'),
    path('notes/export/', views.export_notes_excel, name='export_notes_excel'),


      # URL pour afficher la carte scolaire en HTML
    path(
        'etudiant/<int:etudiant_id>/carte/',
        views.carte_scolaire,
        name='carte_scolaire_html'
    ),

    # URL pour générer la carte scolaire en PDF
    path(
        'etudiant/<int:etudiant_id>/carte/pdf/',
        lambda r, etudiant_id: views.carte_scolaire(r, etudiant_id, pdf=True),
        name='carte_scolaire_pdf'
    ),

    # URL pour vérifier un étudiant via QR code
    path(
        'verifier_etudiant/<int:etudiant_id>/',
        views.verifier_etudiant,
        name='verifier_etudiant'
    ),
    path('certificats/creer/', views.creer_certificat_interface, name='creer_certificat_interface'),
    


]


