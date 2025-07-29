# dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.http import HttpResponse
from django.db import transaction # Pour gérer les transactions de base de données
from django.forms import modelformset_factory # Pour gérer plusieurs formulaires d'un même modèle
from django.forms import formset_factory
from django.utils import timezone
# Pour la génération de PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from datetime import datetime
from datetime import date


from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle

# Importez tous vos formulaires
from .forms import (
    EtudiantForm, DossierInscriptionImageForm, NoteForm, PaiementForm, PresenceForm,
    EnseignantForm, MatiereForm, ClasseForm, ProgrammeMatiereForm, AnneeScolaireForm
)

# Importez tous vos modèles
from .models import (
    Etudiant, AnneeScolaire, Enseignant, Classe, Matiere, ProgrammeMatiere,
    Note, Paiement, Presence, DossierInscriptionImage, CertificatFrequentation
)

from django.db.models import Q  # Pour les recherches complexes

@login_required
def recherche_etudiants(request):
    query = request.GET.get('q', '')
    resultats = []

    if query:
        resultats = Etudiant.objects.filter(
            Q(nom__icontains=query) |
            Q(prenom__icontains=query) |
            Q(numero_matricule__icontains=query) |
            Q(classe__nom_classe__icontains=query)
        ).select_related('classe', 'annee_scolaire_inscription')

    context = {
        'query': query,
        'resultats': resultats,
    }
    return render(request, 'dashboard/etudiants/recherche_etudiants.html', context)


# --- Vues du Dashboard Général ---
@login_required

def dashboard_accueil(request):
    context = {}

    # Assurez-vous que le champ est 'active' comme défini dans votre modèle AnneeScolaire
    annee_active = AnneeScolaire.objects.filter(active=True).first()

    if not annee_active:
        messages.warning(request, "Aucune année scolaire active n'est définie. Veuillez en créer une.")
        # Redirection vers la liste des années scolaires si aucune n'est active
        return redirect('liste_annees_scolaires')

    # Calcul du nombre d'élèves avec paiements impayés ou partiels
    eleves_non_payes_compte = Paiement.objects.filter(
        annee_scolaire=annee_active,
        statut__in=['Impayé', 'Partiel']
    ).values('etudiant').annotate(total_du_par_etudiant=Sum('montant_du')).count() # Compte les étudiants distincts

    # Calcul du nombre d'absents aujourd'hui
    absents_aujourd_hui = Presence.objects.filter(
        date=timezone.now().date(),
        annee_scolaire=annee_active,
        statut='Absent'
    ).count()

    # CALCUL DU TOTAL PAYÉ : Utilise le champ 'montant' de votre modèle Paiement
    total_paye = Paiement.objects.filter(
        annee_scolaire=annee_active,
        statut__in=['Payé', 'Partiel'] # Incluez 'Partiel' si le montant payé sur un paiement partiel est inclus dans le total
    ).aggregate(total_paid=Sum('montant'))['total_paid'] or 0

    # CALCUL DU TOTAL IMPAYÉ : Utilise le champ 'montant_du' de votre modèle Paiement
    total_impaye = Paiement.objects.filter(
        annee_scolaire=annee_active,
        statut__in=['Impayé', 'Partiel']
    ).aggregate(total_due=Sum('montant_du'))['total_due'] or 0

    # Étudiants récemment inscrits (les 3 derniers pour l'année active)
    etudiants_recents = Etudiant.objects.filter(annee_scolaire_inscription=annee_active).order_by('-date_inscription')[:3]

    # Nombre de classes actives pour l'année scolaire active
    classes_actives = Classe.objects.filter(annee_scolaire=annee_active).count()

    # Nombre total d'enseignants (ajuster si vous voulez filtrer par année active)
    enseignants_actifs = Enseignant.objects.all().count()

    context = {
        'annee_active': annee_active,
        'eleves_non_payes_compte': eleves_non_payes_compte,
        'absents_aujourd_hui': absents_aujourd_hui,
        'total_paye': total_paye,
        'total_impaye': total_impaye,
        'etudiants_recents': etudiants_recents,
        'classes_actives': classes_actives,
        'enseignants_actifs': enseignants_actifs,
    }
    return render(request, 'dashboard/dashboard_accueil.html', context)


# --- CRUD pour Etudiant ---

@login_required
def liste_etudiants(request):
    # Start with all students, optimized with select_related for related data
    etudiants = Etudiant.objects.all().select_related('classe', 'annee_scolaire_inscription')

    # Get all classes for the filter dropdown in the template
    toutes_les_classes = Classe.objects.all().order_by('nom_classe')

    # Get the selected class ID from the URL's query parameters (e.g., /eleves/?classe=1)
    selected_classe_id = request.GET.get('classe')

    # Apply the filter if a class ID is provided and is valid
    if selected_classe_id:
        try:
            # Convert the ID to an integer
            selected_classe_id = int(selected_classe_id)
            # Filter the students by the selected class's ID
            etudiants = etudiants.filter(classe__id=selected_classe_id)
        except (ValueError, TypeError):
            # If the provided 'classe' parameter is not a valid integer
            messages.warning(request, "Le filtre de classe sélectionné n'est pas valide.")
            selected_classe_id = None # Reset to show all students if the ID is invalid

    # Order the final queryset for consistent display
    etudiants = etudiants.order_by('classe__nom_classe', 'nom', 'prenom')

    context = {
        'etudiants': etudiants,
        'toutes_les_classes': toutes_les_classes,
        'selected_classe_id': selected_classe_id # Pass this to the template to keep the dropdown selected
    }
    return render(request, 'dashboard/etudiants/liste_etudiants.html', context)

@login_required
def creer_etudiant(request):
    DossierFormSet = modelformset_factory(DossierInscriptionImage, form=DossierInscriptionImageForm, extra=3, can_delete=True)

    if request.method == 'POST':
        form = EtudiantForm(request.POST, request.FILES)
        formset = DossierFormSet(request.POST, request.FILES, queryset=DossierInscriptionImage.objects.none())
        if form.is_valid() and formset.is_valid():
            with transaction.atomic(): # Assure que tout est sauvegardé ou rien
                etudiant = form.save()
                for f in formset:
                    if f.cleaned_data and not f.cleaned_data.get('DELETE'):
                        dossier_image = f.save(commit=False)
                        dossier_image.etudiant = etudiant
                        dossier_image.save()
                messages.success(request, f"L'élève {etudiant.prenom} {etudiant.nom} a été ajouté avec succès.")
                return redirect('detail_etudiant', etudiant_id=etudiant.pk)
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = EtudiantForm()
        formset = DossierFormSet(queryset=DossierInscriptionImage.objects.none())

    return render(request, 'dashboard/etudiants/creer_etudiant.html', {
        'form': form,
        'formset': formset,
    })

@login_required
def detail_etudiant(request, etudiant_id):
    etudiant = get_object_or_404(Etudiant.objects.select_related('classe', 'annee_scolaire_inscription'), pk=etudiant_id)
    dossier_images = etudiant.dossier_images.all() # Récupère les images liées
    notes = Note.objects.filter(etudiant=etudiant).select_related('matiere', 'annee_scolaire').order_by('-annee_scolaire', 'periode_evaluation')
    paiements = Paiement.objects.filter(etudiant=etudiant).select_related('annee_scolaire').order_by('-date_paiement')
    presences = Presence.objects.filter(etudiant=etudiant).select_related('annee_scolaire', 'matiere').order_by('-date')

    # Calcul des totaux de paiement
    total_paye = paiements.filter(statut__in=['Payé', 'Partiel']).aggregate(Sum('montant'))['montant__sum'] or 0
    total_du = paiements.aggregate(Sum('montant_du'))['montant_du__sum'] or 0
    solde_restant = total_du - total_paye

    # Calcul des statistiques de présence
    total_jours_presents = presences.filter(statut='Présent').count()
    total_jours_absents = presences.filter(statut='Absent').count()
    total_jours_retard = presences.filter(statut='Retard').count()
    total_jours_excuses = presences.filter(statut='Excusé').count()


    context = {
        'etudiant': etudiant,
        'dossier_images': dossier_images,
        'notes': notes,
        'paiements': paiements,
        'presences': presences,
        'total_paye': total_paye,
        'total_du': total_du,
        'solde_restant': solde_restant,
        'total_jours_presents': total_jours_presents,
        'total_jours_absents': total_jours_absents,
        'total_jours_retard': total_jours_retard,
        'total_jours_excuses': total_jours_excuses,
    }
    return render(request, 'dashboard/etudiants/detail_etudiant.html', context)

@login_required
def modifier_etudiant(request, etudiant_id):
    etudiant = get_object_or_404(Etudiant, pk=etudiant_id)
    DossierFormSet = modelformset_factory(DossierInscriptionImage, form=DossierInscriptionImageForm, extra=1, can_delete=True)

    if request.method == 'POST':
        form = EtudiantForm(request.POST, request.FILES, instance=etudiant)
        formset = DossierFormSet(request.POST, request.FILES, queryset=DossierInscriptionImage.objects.filter(etudiant=etudiant))
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                etudiant = form.save()
                for f in formset:
                    if f.cleaned_data:
                        if f.cleaned_data.get('DELETE'):
                            if f.instance.pk:
                                f.instance.delete()
                        else:
                            dossier_image = f.save(commit=False)
                            dossier_image.etudiant = etudiant
                            dossier_image.save()
                messages.success(request, f"Les informations de {etudiant.prenom} {etudiant.nom} ont été mises à jour.")
                return redirect('detail_etudiant', etudiant_id=etudiant.pk)
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = EtudiantForm(instance=etudiant)
        formset = DossierFormSet(queryset=DossierInscriptionImage.objects.filter(etudiant=etudiant))

    return render(request, 'dashboard/etudiants/modifier_etudiant.html', {
        'form': form,
        'formset': formset,
        'etudiant': etudiant
    })

@login_required
def supprimer_etudiant(request, etudiant_id):
    etudiant = get_object_or_404(Etudiant, pk=etudiant_id)
    if request.method == 'POST':
        nom_complet = f"{etudiant.prenom} {etudiant.nom}"
        etudiant.delete()
        messages.success(request, f"L'élève {nom_complet} a été supprimé avec succès.")
        return redirect('liste_etudiants')
    return render(request, 'dashboard/etudiants/confirmer_suppression_etudiant.html', {'etudiant': etudiant})

# --- Vues pour les notes, paiements, présences (création/modification liée à un élève) ---
# Vous pouvez les créer comme des vues séparées ou des modales dans la page de détail de l'élève

@login_required
def ajouter_note(request, etudiant_id):
    etudiant = get_object_or_404(Etudiant, pk=etudiant_id)
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.etudiant = etudiant # Associe la note à l'élève actuel
            note.save()
            messages.success(request, "Note ajoutée avec succès.")
            return redirect('detail_etudiant', etudiant_id=etudiant.pk)
    else:
        form = NoteForm(initial={'etudiant': etudiant}) # Pré-remplit l'élève
    return render(request, 'dashboard/etudiants/ajouter_note.html', {'form': form, 'etudiant': etudiant})

# ... créer modifier_note, supprimer_note, ajouter_paiement, modifier_paiement, etc. sur le même principe

# --- Génération de Certificat de Fréquentation ---
@login_required
def generer_certificat_frequentation(request, etudiant_id):
    etudiant = get_object_or_404(Etudiant, pk=etudiant_id)
    annee_scolaire_active = AnneeScolaire.objects.filter(active=True).first()
    if not annee_scolaire_active:
        messages.error(request, "Impossible de générer le certificat : Aucune année scolaire active définie.")
        return redirect('detail_etudiant', etudiant_id=etudiant.pk)

    # Vérification de la fréquentation (simplifié ici, à améliorer)
    # Ex: au moins N présences ou un pourcentage X%
    nombre_presences = Presence.objects.filter(
        etudiant=etudiant,
        annee_scolaire=annee_scolaire_active,
        statut__in=['Présent', 'Retard', 'Excusé']
    ).count()

    # Vous pouvez définir un seuil minimal de présence ici
    if nombre_presences < 50: # Exemple: si moins de 50 jours de présence enregistrés
        messages.warning(request, f"L'élève {etudiant.prenom} {etudiant.nom} n'a pas un nombre suffisant de présences enregistrées ({nombre_presences}) pour l'année {annee_scolaire_active.annee} pour justifier un certificat de fréquentation.")
        # return redirect('detail_etudiant', etudiant_id=etudiant.pk)
        # Ou laisser passer avec un avertissement si c'est la politique

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificat_{etudiant.nom}_{etudiant.prenom}_{annee_scolaire_active.annee}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    styles = getSampleStyleSheet()

    # En-tête
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2.0, height - 50, "RÉPUBLIQUE DU MALI")
    p.drawCentredString(width/2.0, height - 70, "MINISTÈRE DE L'ÉDUCATION NATIONALE")
    p.setFont("Helvetica", 12)
    p.drawCentredString(width/2.0, height - 90, "[Nom de votre École / Académie d'Enseignement]")
    p.drawCentredString(width/2.0, height - 110, "[Adresse de l'École]")

    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width/2.0, height - 180, "CERTIFICAT DE FRÉQUENTATION SCOLAIRE")

    p.setFont("Helvetica", 12)
    textobject = p.beginText()
    textobject.setTextOrigin(100, height - 250)
    textobject.textLine("Nous soussignés, Direction de [Nom de votre École], certifions que l'élève :")

    textobject.textLine("") # Ligne vide
    textobject.setFont("Helvetica-Bold", 14)
    textobject.textLine(f"   Nom et Prénom(s) : {etudiant.nom.upper()} {etudiant.prenom.upper()}")
    textobject.textLine(f"   Date et lieu de naissance : {etudiant.date_naissance.strftime('%d/%m/%Y')} à {etudiant.lieu_naissance or 'Non renseigné'}")
    textobject.textLine(f"   Sexe : {'Masculin' if etudiant.genre == 'M' else 'Féminin'}")
    textobject.textLine(f"   Numéro Matricule : {etudiant.numero_matricule or 'Non attribué'}")

    textobject.textLine("")
    textobject.setFont("Helvetica", 12)
    textobject.textLine(f"A bien fréquenté notre établissement, en classe de ")
    textobject.setFont("Helvetica-Bold", 14)
    textobject.textLine(f"   {etudiant.classe.nom_classe or 'Non assignée'} ")
    textobject.textLine("")
    textobject.setFont("Helvetica", 12)
    textobject.textLine(f"Au cours de l'année scolaire :")
    textobject.setFont("Helvetica-Bold", 14)
    textobject.textLine(f"   {annee_scolaire_active.annee}")

    textobject.textLine("")
    textobject.setFont("Helvetica", 10)
    textobject.textLine(f"En foi de quoi, le présent certificat est délivré pour servir et valoir ce que de droit.")
    textobject.textLine("")
    textobject.textLine(f"Fait à [Votre Ville au Mali], le {datetime.now().strftime('%d %B %Y')}.") # Date complète
    textobject.textLine("")
    textobject.textLine("")
    textobject.textLine("Le Directeur/La Directrice,")
    textobject.textLine("")
    textobject.textLine("[Nom et Prénom du Directeur/Directrice]") # À rendre dynamique si vous avez un modèle pour le personnel de l'école

    p.drawText(textobject)

    # Enregistrer le certificat en BD (facultatif mais recommandé)
    certificat, created = CertificatFrequentation.objects.get_or_create(
        etudiant=etudiant,
        annee_scolaire=annee_scolaire_active,
        defaults={
            'date_delivrance': timezone.now().date(),
            'delivre_par': request.user,
            'numero_certificat': f"CERT-{etudiant.numero_matricule or etudiant.pk}-{annee_scolaire_active.annee}" # Générer un numéro unique
        }
    )
    # Si le fichier PDF est sauvegardé sur le serveur, vous pouvez le lier ici
    # certificat.fichier_pdf.save(response['Content-Disposition'].split('filename="')[1][:-1], ContentFile(p.getpdfdata())) # Nécessite ContentFile from django.core.files.base

    p.showPage()
    p.save()
    messages.success(request, f"Certificat de fréquentation généré pour {etudiant.prenom} {etudiant.nom}.")
    return response

# --- Génération de Bulletin Scolaire ---
def generer_bulletin_scolaire(request, etudiant_id, periode): # Ex: periode = 'Trimestre 1' ou 'Annuelle'
    etudiant = get_object_or_404(Etudiant, pk=etudiant_id)
    annee_scolaire_active = AnneeScolaire.objects.filter(active=True).first() # Ou passer l'ID de l'année en paramètre
    if not annee_scolaire_active:
        messages.error(request, "Impossible de générer le bulletin : Aucune année scolaire active définie.")
        return redirect('detail_etudiant', etudiant_id=etudiant.pk)

    # Récupérer les notes de l'étudiant pour la période et l'année scolaire
    notes_etudiant = Note.objects.filter(
        etudiant=etudiant,
        periode_evaluation=periode,
        annee_scolaire=annee_scolaire_active
    ).select_related('matiere').order_by('matiere__nom')

    # Récupérer les coefficients pour les matières de la classe de l'étudiant
    programmes_matiere = ProgrammeMatiere.objects.filter(
        classe=etudiant.classe,
        matiere__in=[n.matiere for n in notes_etudiant] # Ne prendre que les matières pour lesquelles il y a des notes
    ).select_related('matiere')

    # Créer un dictionnaire de coefficients {matiere_id: coefficient}
    coefficients = {pm.matiere.pk: pm.coefficient for pm in programmes_matiere}

    # Préparer les données pour le tableau du bulletin
    data = [['Matière', 'Coeff.', 'Note/20', 'Total Points']]
    total_points_general = 0
    total_coefficients_general = 0

    for note in notes_etudiant:
        coeff = coefficients.get(note.matiere.pk, 1) # Récupère le coefficient, 1 par défaut
        points_matiere = note.valeur * coeff
        data.append([
            note.matiere.nom,
            str(coeff),
            f"{note.valeur:.2f}",
            f"{points_matiere:.2f}"
        ])
        total_points_general += points_matiere
        total_coefficients_general += coeff

    moyenne_generale = total_points_general / total_coefficients_general if total_coefficients_general > 0 else 0

    data.append(['', '', 'Total Coeff.', total_coefficients_general])
    data.append(['', '', 'Moyenne Générale', f"{moyenne_generale:.2f}"])


    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bulletin_{etudiant.nom}_{etudiant.prenom}_{periode.replace(" ", "_")}_{annee_scolaire_active.annee}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    styles = getSampleStyleSheet()

    # En-tête du bulletin
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2.0, height - 50, "RÉPUBLIQUE DU MALI")
    p.drawCentredString(width/2.0, height - 70, "MINISTÈRE DE L'ÉDUCATION NATIONALE")
    p.setFont("Helvetica", 12)
    p.drawCentredString(width/2.0, height - 90, "[Nom de votre École / Académie d'Enseignement]")
    p.drawCentredString(width/2.0, height - 110, "[Adresse de l'École]")

    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2.0, height - 150, "BULLETIN DE NOTES")
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 180, f"Année Scolaire : {annee_scolaire_active.annee}")
    p.drawString(100, height - 200, f"Période : {periode}")

    p.drawString(100, height - 230, f"Élève : {etudiant.prenom} {etudiant.nom}")
    p.drawString(100, height - 250, f"Classe : {etudiant.classe.nom_classe}")
    p.drawString(100, height - 270, f"Numéro Matricule : {etudiant.numero_matricule or 'Non attribué'}")

    # Table des notes
    table = Table(data, colWidths=[200, 50, 70, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ADD8E6')), # Bleu clair pour l'en-tête
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -3), colors.white), # Pour les lignes de données
        ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor('#D3D3D3')), # Gris clair pour les totaux/moyennes
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (0, len(data)-1), (1, len(data)-1)), # Moyenne Générale
        ('SPAN', (0, len(data)-2), (1, len(data)-2)), # Total Coeff.
        ('ALIGN', (0, len(data)-1), (2, len(data)-1), 'RIGHT'), # Texte 'Moyenne Générale' à droite
        ('ALIGN', (0, len(data)-2), (2, len(data)-2), 'RIGHT'), # Texte 'Total Coeff.' à droite
        ('FONTNAME', (0, len(data)-1), (-1, len(data)-1), 'Helvetica-Bold'),
        ('FONTNAME', (0, len(data)-2), (-1, len(data)-2), 'Helvetica-Bold'),

    ]))

    # Calculer la hauteur de la table pour la positionner
    table_height = table.wrapOn(p, width, height)[1]
    table.drawOn(p, 80, height - 300 - table_height) # Positionner la table

    # Appréciations (vous devrez ajouter un modèle pour les appréciations ou les gérer manuellement)
    # Par exemple, un champ TextField dans le modèle Bulletin, ou une relation ManyToMany avec un modèle Appréciation
    p.setFont("Helvetica-Bold", 12)
    p.drawString(80, height - 300 - table_height - 30, "Appréciations du Conseil de Classe :")
    appreciation_text = "Élève sérieux et assidu, avec des progrès significatifs dans toutes les matières. Encouragements à maintenir cet effort."
    p.setFont("Helvetica", 10)
    p.drawString(80, height - 300 - table_height - 50, appreciation_text) # À rendre dynamique

    # Signature
    p.setFont("Helvetica", 10)
    p.drawString(80, 100, f"Fait à [Votre Ville au Mali], le {datetime.now().strftime('%d %B %Y')}.")
    p.drawString(80, 80, "Le Directeur/La Directrice,")
    p.drawString(80, 60, "[Nom et Prénom du Directeur/Directrice]")

    p.showPage()
    p.save()
    messages.success(request, f"Bulletin de notes généré pour {etudiant.prenom} {etudiant.nom} pour {periode}.")
    return response


@login_required # Optionnel : protège cette vue aux utilisateurs connectés
def liste_paiements_par_classe_etudiant(request):
    # 1. Obtenir l'année scolaire active
    annee_active = AnneeScolaire.objects.filter(active=True).first()
    
    # Récupérer toutes les classes pour le filtre (toujours nécessaire, même sans filtre actif)
    toutes_les_classes = Classe.objects.all().order_by('nom_classe')

    # Récupérer les paramètres de filtre depuis la requête GET
    selected_classe_id = request.GET.get('classe_filter_id')
    selected_statut = request.GET.get('statut_filter') # Nouveau filtre de statut

    try:
        selected_classe_id = int(selected_classe_id) if selected_classe_id else None
    except ValueError:
        selected_classe_id = None # En cas de valeur invalide dans l'URL

    data_par_classe = [] # Liste qui contiendra toutes nos données structurées pour le template

    if annee_active:
        # Requêtes de base pour les étudiants et paiements de l'année active
        etudiants_query = Etudiant.objects.filter(annee_scolaire_inscription=annee_active).select_related('classe')
        paiements_query = Paiement.objects.filter(annee_scolaire=annee_active).select_related('etudiant__classe', 'etudiant')

        # Appliquer le filtre de classe si sélectionné
        if selected_classe_id:
            etudiants_query = etudiants_query.filter(classe__id=selected_classe_id)
            paiements_query = paiements_query.filter(etudiant__classe__id=selected_classe_id)
            # Si une classe est sélectionnée, on ne traite que cette classe
            classes_a_traiter = Classe.objects.filter(id=selected_classe_id)
        else:
            # Toutes les classes si pas de filtre par classe
            classes_a_traiter = toutes_les_classes 

        # Appliquer le filtre de statut si sélectionné
        if selected_statut == 'impayes_partiels':
            paiements_query = paiements_query.filter(statut__in=['Impayé', 'Partiel'])
        elif selected_statut == 'payes':
            paiements_query = paiements_query.filter(statut='Payé')

        # Exécuter les requêtes après application des filtres et les ordonner
        tous_les_etudiants_annee_active = etudiants_query.order_by('nom', 'prenom')
        tous_les_paiements_annee_active = paiements_query.order_by('etudiant__nom', 'etudiant__prenom', 'date_paiement')

        # Créer des dictionnaires pour un accès rapide aux données par ID (optimisation)
        etudiants_par_classe_id = {cls.id: [] for cls in classes_a_traiter}
        for etudiant in tous_les_etudiants_annee_active:
            # S'assurer que l'élève a une classe assignée et que cette classe est dans notre liste à traiter
            if etudiant.classe_id and etudiant.classe_id in etudiants_par_classe_id:
                etudiants_par_classe_id[etudiant.classe.id].append(etudiant)

        # Les paiements sont toujours séparés en 'payes' et 'impayes_partiels' pour l'affichage détaillé,
        # même si la 'paiements_query' a déjà été filtrée par statut.
        paiements_par_etudiant_id = {etudiant.id: {'payes': [], 'impayes_partiels': []} for etudiant in tous_les_etudiants_annee_active}
        for paiement in tous_les_paiements_annee_active:
            if paiement.etudiant_id:
                if paiement.statut == 'Payé':
                    paiements_par_etudiant_id[paiement.etudiant.id]['payes'].append(paiement)
                else: # 'Impayé' ou 'Partiel'
                    paiements_par_etudiant_id[paiement.etudiant.id]['impayes_partiels'].append(paiement)

        # Construire la structure finale des données pour le template
        for classe in classes_a_traiter:
            etudiants_data_dans_classe = []
            etudiants_actuels_de_la_classe = etudiants_par_classe_id.get(classe.id, [])

            for etudiant in etudiants_actuels_de_la_classe:
                paiements_de_cet_etudiant = paiements_par_etudiant_id.get(etudiant.id, {'payes': [], 'impayes_partiels': []})
                
                # IMPORTANT : Filtrer les paiements pour les totaux aussi
                # afin que les totaux reflètent le filtre de statut appliqué.
                # Si le filtre de statut est 'impayes_partiels', nous ne sommons que ces derniers.
                # Si le filtre est 'payes', nous ne sommons que ceux-là.
                # Sinon (tous les statuts), nous sommons tout.
                paiements_pour_totaux = []
                if selected_statut == 'impayes_partiels':
                    paiements_pour_totaux = paiements_de_cet_etudiant['impayes_partiels']
                elif selected_statut == 'payes':
                    paiements_pour_totaux = paiements_de_cet_etudiant['payes']
                else: # Tous les statuts (ou pas de filtre statut)
                    paiements_pour_totaux = paiements_de_cet_etudiant['payes'] + paiements_de_cet_etudiant['impayes_partiels']

                total_du_etudiant = sum(p.montant_du for p in paiements_pour_totaux)
                total_paye_etudiant = sum(p.montant for p in paiements_pour_totaux)
                
                # Ajouter l'élève à la liste seulement s'il a des paiements *visibles* avec les filtres actuels.
                # Cela évite d'afficher des élèves sans paiements correspondants au filtre.
                if paiements_de_cet_etudiant['payes'] or paiements_de_cet_etudiant['impayes_partiels']:
                    etudiants_data_dans_classe.append({
                        'etudiant': etudiant,
                        'total_du': total_du_etudiant,
                        'total_paye': total_paye_etudiant,
                        'paiements_payes': paiements_de_cet_etudiant['payes'],
                        'paiements_impayes_partiels': paiements_de_cet_etudiant['impayes_partiels'],
                    })
            
            # N'ajouter la classe que si elle a des élèves avec des paiements qui correspondent aux filtres
            if etudiants_data_dans_classe:
                data_par_classe.append({
                    'classe': classe,
                    'etudiants_data': etudiants_data_dans_classe
                })
                
    context = {
        'annee_active': annee_active,
        'data_par_classe': data_par_classe,
        'toutes_les_classes': toutes_les_classes, # Pour le filtre de classe dans le template
        'selected_classe_id': selected_classe_id, # Pour maintenir la sélection du filtre de classe
        'selected_statut': selected_statut,       # Pour maintenir la sélection du filtre de statut
    }
    # Assurez-vous que le chemin du template est correct.
    # Si votre template est dans 'dashboard/templates/dashboard/paiements/paiements_par_classe_etudiant.html',
    # le chemin ici doit être 'dashboard/paiements/paiements_par_classe_etudiant.html'
    return render(request, 'dashboard/paiements/paiements_par_classe_etudiant.html', context)


@login_required # Optional: Protect this view
def liste_paiements_impayes(request):
    # 1. Trouver l'année scolaire active
    annee_active = AnneeScolaire.objects.filter(active=True).first()

    paiements_impayes = []
    if annee_active:
        # 2. Filtrer les paiements pour cette année scolaire
        # 3. Filtrer par statut 'Impayé' ou 'Partiel'
        paiements_impayes = Paiement.objects.filter(
            annee_scolaire=annee_active
        ).filter(
            statut__in=['Impayé', 'Partiel'] # Use __in for multiple choices
        ).order_by('etudiant__nom', 'etudiant__prenom', 'date_paiement') # Order for better readability

    context = {
        'paiements_impayes': paiements_impayes,
        'annee_active': annee_active, # Passe l'année active au template
    }
    return render(request, 'dashboard/paiements/paiements_impayes.html', context)


@login_required # Optional: Protect this view
def liste_paiements_payes(request):
    # 1. Find the active school year
    annee_active = AnneeScolaire.objects.filter(active=True).first()

    paiements_payes = []
    if annee_active:
        # 2. Filter payments for this school year that are 'Payé'
        paiements_payes = Paiement.objects.filter(
            annee_scolaire=annee_active,
            statut='Payé' # Filter specifically for 'Payé' status
        ).order_by('etudiant__nom', 'etudiant__prenom', '-date_paiement') # Order by student and most recent payment first

    context = {
        'paiements_payes': paiements_payes,
        'annee_active': annee_active, # Pass the active year to the template
    }
    return render(request, 'dashboard/paiements/paiements_payes.html', context)


# --- CRUD pour les Années Scolaires ---
@login_required
def liste_annees_scolaires(request):
    annees_scolaires = AnneeScolaire.objects.all().order_by('-annee')

    # --- Logique pour déterminer l'année civile et l'année scolaire actuelle ---
    current_calendar_year = datetime.now().year
    current_month = datetime.now().month

    # Logique pour déterminer l'année scolaire suggérée (comme dans votre formulaire)
    if current_month >= 8: # Si l'année scolaire commence en août (à ajuster selon votre besoin)
        current_academic_start_year = current_calendar_year
        current_academic_end_year = current_calendar_year + 1
    else: # Si elle a commencé l'année précédente
        current_academic_start_year = current_calendar_year - 1
        current_academic_end_year = current_calendar_year
    
    current_academic_year_string = f"{current_academic_start_year}-{current_academic_end_year}"
    # -------------------------------------------------------------------------

    context = {
        'annees_scolaires': annees_scolaires,
        'current_calendar_year': current_calendar_year,
        'current_academic_year_string': current_academic_year_string,
    }
    return render(request, 'dashboard/annees_scolaires/liste_annees_scolaires.html', context)
@login_required
def creer_annee_scolaire(request):
    if request.method == 'POST':
        form = AnneeScolaireForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Année scolaire ajoutée avec succès.")
            return redirect('liste_annees_scolaires')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = AnneeScolaireForm()
    return render(request, 'dashboard/annees_scolaires/form_annee_scolaire.html', {'form': form, 'action': 'Créer'})

@login_required
def modifier_annee_scolaire(request, pk):
    annee = get_object_or_404(AnneeScolaire, pk=pk)
    if request.method == 'POST':
        form = AnneeScolaireForm(request.POST, instance=annee)
        if form.is_valid():
            form.save()
            messages.success(request, "Année scolaire mise à jour avec succès.")
            return redirect('liste_annees_scolaires')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = AnneeScolaireForm(instance=annee)
    return render(request, 'dashboard/annees_scolaires/form_annee_scolaire.html', {'form': form, 'action': 'Modifier'})

@login_required
def supprimer_annee_scolaire(request, pk):
    annee = get_object_or_404(AnneeScolaire, pk=pk)
    if request.method == 'POST':
        annee_nom = annee.annee
        annee.delete()
        messages.success(request, f"L'année scolaire {annee_nom} a été supprimée.")
        return redirect('liste_annees_scolaires')
    return render(request, 'dashboard/annees_scolaires/confirmer_suppression_annee_scolaire.html', {'annee': annee})

# --- CRUD pour les Classes ---
@login_required
def liste_classes(request):
    classes = Classe.objects.all().select_related('annee_scolaire', 'enseignant_principal').order_by('annee_scolaire', 'nom_classe')
    return render(request, 'dashboard/classes/liste_classes.html', {'classes': classes})

@login_required
def creer_classe(request):
    if request.method == 'POST':
        form = ClasseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Classe ajoutée avec succès.")
            return redirect('liste_classes')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = ClasseForm()
    return render(request, 'dashboard/classes/form_classe.html', {'form': form, 'action': 'Créer'})

@login_required
def modifier_classe(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    if request.method == 'POST':
        form = ClasseForm(request.POST, instance=classe)
        if form.is_valid():
            form.save()
            messages.success(request, "Classe mise à jour avec succès.")
            return redirect('liste_classes')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = ClasseForm(instance=classe)
    return render(request, 'dashboard/classes/form_classe.html', {'form': form, 'action': 'Modifier'})

@login_required
def supprimer_classe(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    if request.method == 'POST':
        classe_nom = classe.nom_classe
        classe.delete()
        messages.success(request, f"La classe {classe_nom} a été supprimée.")
        return redirect('liste_classes')
    return render(request, 'dashboard/classes/confirmer_suppression_classe.html', {'classe': classe})

# --- CRUD pour les Matières ---
@login_required
def liste_matieres(request):
    matieres = Matiere.objects.all().order_by('nom')
    return render(request, 'dashboard/matieres/liste_matieres.html', {'matieres': matieres})

@login_required
def creer_matiere(request):
    if request.method == 'POST':
        form = MatiereForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Matière ajoutée avec succès.")
            return redirect('liste_matieres')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = MatiereForm()
    return render(request, 'dashboard/matieres/form_matiere.html', {'form': form, 'action': 'Créer'})

@login_required
def modifier_matiere(request, pk):
    matiere = get_object_or_404(Matiere, pk=pk)
    if request.method == 'POST':
        form = MatiereForm(request.POST, instance=matiere)
        if form.is_valid():
            form.save()
            messages.success(request, "Matière mise à jour avec succès.")
            return redirect('liste_matieres')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = MatiereForm(instance=matiere)
    return render(request, 'dashboard/matieres/form_matiere.html', {'form': form, 'action': 'Modifier'})

@login_required
def supprimer_matiere(request, pk):
    matiere = get_object_or_404(Matiere, pk=pk)
    if request.method == 'POST':
        matiere_nom = matiere.nom
        matiere.delete()
        messages.success(request, f"La matière {matiere_nom} a été supprimée.")
        return redirect('liste_matieres')
    return render(request, 'dashboard/matieres/confirmer_suppression_matiere.html', {'matiere': matiere})

# --- CRUD pour les Enseignants ---
@login_required
def liste_enseignants(request):
    enseignants = Enseignant.objects.all().order_by('nom', 'prenom')
    return render(request, 'dashboard/enseignants/liste_enseignants.html', {'enseignants': enseignants})

@login_required
def creer_enseignant(request):
    if request.method == 'POST':
        form = EnseignantForm(request.POST)
        if form.is_valid():
            enseignant = form.save()
            messages.success(request, f"L'enseignant {enseignant.prenom} {enseignant.nom} a été ajouté avec succès.")
            return redirect('liste_enseignants')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = EnseignantForm()
    return render(request, 'dashboard/enseignants/form_enseignant.html', {'form': form, 'action': 'Créer'})

@login_required
def modifier_enseignant(request, pk):
    enseignant = get_object_or_404(Enseignant, pk=pk)
    if request.method == 'POST':
        form = EnseignantForm(request.POST, instance=enseignant)
        if form.is_valid():
            form.save()
            messages.success(request, f"L'enseignant {enseignant.prenom} {enseignant.nom} a été mis à jour.")
            return redirect('liste_enseignants')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = EnseignantForm(instance=enseignant)
    return render(request, 'dashboard/enseignants/form_enseignant.html', {'form': form, 'action': 'Modifier'})

@login_required
def supprimer_enseignant(request, pk):
    enseignant = get_object_or_404(Enseignant, pk=pk)
    if request.method == 'POST':
        nom_complet = f"{enseignant.prenom} {enseignant.nom}"
        enseignant.delete()
        messages.success(request, f"L'enseignant {nom_complet} a été supprimé.")
        return redirect('liste_enseignants')
    return render(request, 'dashboard/enseignants/confirmer_suppression_enseignant.html', {'enseignant': enseignant})


# --- CRUD pour les Programmes Matières (affectation de matières/coefficients aux classes) ---
@login_required
def liste_programmes_matiere(request):
    annee_active = AnneeScolaire.objects.filter(active=True).first()
    if not annee_active:
        messages.warning(request, "Aucune année scolaire active n'est définie. Veuillez en créer une.")
        return redirect('liste_annees_scolaires')

    programmes = ProgrammeMatiere.objects.filter(classe__annee_scolaire=annee_active).select_related('classe', 'matiere', 'enseignant').order_by('classe__nom_classe', 'matiere__nom')
    return render(request, 'dashboard/programmes_matiere/liste_programmes_matiere.html', {'programmes': programmes, 'annee_active': annee_active})

@login_required
def creer_programme_matiere(request):
    if request.method == 'POST':
        form = ProgrammeMatiereForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Programme matière ajouté avec succès.")
            return redirect('liste_programmes_matiere')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = ProgrammeMatiereForm()
    return render(request, 'dashboard/programmes_matiere/form_programme_matiere.html', {'form': form, 'action': 'Créer'})

@login_required
def modifier_programme_matiere(request, pk):
    programme = get_object_or_404(ProgrammeMatiere, pk=pk)
    if request.method == 'POST':
        form = ProgrammeMatiereForm(request.POST, instance=programme)
        if form.is_valid():
            form.save()
            messages.success(request, "Programme matière mis à jour avec succès.")
            return redirect('liste_programmes_matiere')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = ProgrammeMatiereForm(instance=programme)
    return render(request, 'dashboard/programmes_matiere/form_programme_matiere.html', {'form': form, 'action': 'Modifier'})

@login_required
def supprimer_programme_matiere(request, pk):
    programme = get_object_or_404(ProgrammeMatiere, pk=pk)
    if request.method == 'POST':
        nom_complet = f"{programme.matiere.nom} pour {programme.classe.nom_classe}"
        programme.delete()
        messages.success(request, f"Le programme matière '{nom_complet}' a été supprimé.")
        return redirect('liste_programmes_matiere')
    return render(request, 'dashboard/programmes_matiere/confirmer_suppression_programme_matiere.html', {'programme': programme})

# --- CRUD pour les Notes ---
# Les fonctions ajouter/modifier/supprimer note sont généralement liées à la page détail élève.
# On a déjà ajouter_note ci-dessus. Voici un exemple pour modifier_note.

@login_required
def modifier_note(request, pk):
    note = get_object_or_404(Note, pk=pk)
    etudiant_id = note.etudiant.pk # Pour rediriger après modification
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, "Note modifiée avec succès.")
            return redirect('detail_etudiant', etudiant_id=etudiant_id)
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = NoteForm(instance=note)
    return render(request, 'dashboard/etudiants/modifier_note.html', {'form': form, 'note': note})

@login_required
def supprimer_note(request, pk):
    note = get_object_or_404(Note, pk=pk)
    etudiant_id = note.etudiant.pk
    if request.method == 'POST':
        note.delete()
        messages.success(request, "Note supprimée avec succès.")
        return redirect('detail_etudiant', etudiant_id=etudiant_id)
    return render(request, 'dashboard/etudiants/confirmer_suppression_note.html', {'note': note})


# --- CRUD pour les Paiements ---
@login_required
def ajouter_paiement(request, etudiant_id):
    etudiant = get_object_or_404(Etudiant, pk=etudiant_id)
    if request.method == 'POST':
        form = PaiementForm(request.POST)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.etudiant = etudiant
            paiement.enregistre_par = request.user
            paiement.save()
            messages.success(request, "Paiement ajouté avec succès.")
            return redirect('detail_etudiant', etudiant_id=etudiant.pk)
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = PaiementForm(initial={'etudiant': etudiant, 'annee_scolaire': AnneeScolaire.objects.filter(active=True).first()})
    return render(request, 'dashboard/etudiants/ajouter_paiement.html', {'form': form, 'etudiant': etudiant})

@login_required
def modifier_paiement(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk)
    etudiant_id = paiement.etudiant.pk
    if request.method == 'POST':
        form = PaiementForm(request.POST, instance=paiement)
        if form.is_valid():
            form.save()
            messages.success(request, "Paiement modifié avec succès.")
            return redirect('detail_etudiant', etudiant_id=etudiant_id)
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = PaiementForm(instance=paiement)
    return render(request, 'dashboard/etudiants/modifier_paiement.html', {'form': form, 'paiement': paiement})

@login_required
def supprimer_paiement(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk)
    etudiant_id = paiement.etudiant.pk
    if request.method == 'POST':
        paiement.delete()
        messages.success(request, "Paiement supprimé avec succès.")
        return redirect('detail_etudiant', etudiant_id=etudiant_id)
    return render(request, 'dashboard/etudiants/confirmer_suppression_paiement.html', {'paiement': paiement})

@login_required
def liste_paiements_impayes(request):
    annee_active = AnneeScolaire.objects.filter(active=True).first()
    if not annee_active:
        messages.warning(request, "Aucune année scolaire active n'est définie.")
        return redirect('liste_annees_scolaires')

    paiements_impayes = Paiement.objects.filter(
        annee_scolaire=annee_active,
        statut__in=['Impayé', 'Partiel']
    ).select_related('etudiant', 'etudiant__classe').order_by('etudiant__classe__nom_classe', 'etudiant__nom')

    context = {
        'paiements_impayes': paiements_impayes,
        'annee_active': annee_active
    }
    return render(request, 'dashboard/paiements/liste_paiements_impayes.html', context)


# --- CRUD pour les Présences ---
@login_required
def marquer_presence_classe(request, classe_id):
    matiere_id = request.GET.get('matiere_id')

    classe = get_object_or_404(Classe, pk=classe_id)
    date_aujourdhui = date.today()
    annee_active = AnneeScolaire.objects.filter(active=True).first()

    if not annee_active:
        messages.warning(request, "Veuillez définir une année scolaire active avant de marquer les présences.")
        return redirect('liste_annees_scolaires')

    etudiants_de_la_classe = Etudiant.objects.filter(
        classe=classe,
        annee_scolaire_inscription=annee_active
    ).order_by('nom', 'prenom')

    # 🔍 Appliquer le filtre matière si fourni (si Etudiant a une relation à Matiere)
    if matiere_id:
        etudiants_de_la_classe = etudiants_de_la_classe.filter(matiere_id=matiere_id)

    PresenceFormSet = formset_factory(PresenceForm, extra=0)
    initial_data = []

    existing_presences_list = Presence.objects.filter(
        classe=classe,
        date=date_aujourdhui,
        annee_scolaire=annee_active
    )
    existing_presences = {p.etudiant_id: p for p in existing_presences_list}

    for etudiant in etudiants_de_la_classe:
        if etudiant.id in existing_presences:
            presence_instance = existing_presences[etudiant.id]
            initial_data.append({
                'id': presence_instance.id,
                'etudiant': etudiant,
                'etudiant_obj': etudiant,
                'classe': classe,
                'date': date_aujourdhui,
                'annee_scolaire': annee_active,
                'statut': presence_instance.statut,
                'matiere': presence_instance.matiere.pk if presence_instance.matiere else None,
                'heure_debut_cours': presence_instance.heure_debut_cours,
                'heure_fin_cours': presence_instance.heure_fin_cours,
                'motif_absence_retard': presence_instance.motif_absence_retard,
                'justificatif_fourni': presence_instance.justificatif_fourni,
                'est_present': presence_instance.statut == 'Présent',
                'statut_detail': presence_instance.statut if presence_instance.statut != 'Présent' else '',
            })
        else:
            initial_data.append({
                'etudiant': etudiant,
                'etudiant_obj': etudiant,
                'classe': classe,
                'date': date_aujourdhui,
                'annee_scolaire': annee_active,
                'statut': 'Présent',
                'est_present': True,
                'statut_detail': '',
            })

    if request.method == 'POST':
        formset = PresenceFormSet(request.POST, initial=initial_data)
        if formset.is_valid():
            try:
                with transaction.atomic():
                    for form in formset:
                        est_present = form.cleaned_data.get('est_present')
                        statut_detail_from_form = form.cleaned_data.get('statut_detail')

                        if form.instance.pk:
                            presence_instance = form.instance
                        else:
                            presence_instance = Presence(
                                etudiant=form.cleaned_data['etudiant'],
                                classe=form.cleaned_data['classe'],
                                date=form.cleaned_data['date'],
                                annee_scolaire=form.cleaned_data['annee_scolaire']
                            )

                        if est_present:
                            presence_instance.statut = 'Présent'
                            presence_instance.matiere = None
                            presence_instance.heure_debut_cours = None
                            presence_instance.heure_fin_cours = None
                            presence_instance.motif_absence_retard = ''
                            presence_instance.justificatif_fourni = False
                        else:
                            presence_instance.statut = statut_detail_from_form or 'Absent'
                            presence_instance.matiere = form.cleaned_data.get('matiere')
                            presence_instance.heure_debut_cours = form.cleaned_data.get('heure_debut_cours')
                            presence_instance.heure_fin_cours = form.cleaned_data.get('heure_fin_cours')
                            presence_instance.motif_absence_retard = form.cleaned_data.get('motif_absence_retard', '')
                            presence_instance.justificatif_fourni = form.cleaned_data.get('justificatif_fourni', False)

                        presence_instance.save()

                    messages.success(request, f"La présence pour la classe {classe.nom_classe} a été enregistrée avec succès.")
                    return redirect('liste_classes')
            except Exception as e:
                messages.error(request, f"Une erreur est survenue lors de l'enregistrement : {e}")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        formset = PresenceFormSet(initial=initial_data)

    toutes_les_classes = Classe.objects.all().order_by('nom_classe')
    toutes_les_matieres = Matiere.objects.all().order_by('nom')  # 👈 nécessaire pour ton filtre JS

    context = {
        'classe': classe,
        'date_aujourdhui': date_aujourdhui,
        'formset': formset,
        'annee_active': annee_active,
        'toutes_les_classes': toutes_les_classes,
        'toutes_les_matieres': toutes_les_matieres,
        'matiere_id': matiere_id,  # pour pré-sélectionner la matière dans le <select>
    }
    return render(request, 'dashboard/presences/marquer_presence_classe.html', context)


@login_required
def suivi_presence_classe(request, classe_id):
    classe = get_object_or_404(Classe, pk=classe_id)
    annee_active = AnneeScolaire.objects.filter(active=True).first()

    # Filtrer par date si un filtre est appliqué
    date_filtre = request.GET.get('date')
    if date_filtre:
        try:
            date_filtre = datetime.strptime(date_filtre, '%Y-%m-%d').date()
        except ValueError:
            date_filtre = None

    presences_par_etudiant = {}
    etudiants = Etudiant.objects.filter(classe=classe, annee_scolaire_inscription=annee_active).order_by('nom', 'prenom')

    for etudiant in etudiants:
        presences_query = Presence.objects.filter(etudiant=etudiant, classe=classe, annee_scolaire=annee_active)
        if date_filtre:
            presences_query = presences_query.filter(date=date_filtre)

        presences_etudiant = presences_query.order_by('-date')
        presences_par_etudiant[etudiant] = presences_etudiant

    context = {
        'classe': classe,
        'presences_par_etudiant': presences_par_etudiant,
        'date_filtre': date_filtre,
        'annee_active': annee_active
    }
    return render(request, 'dashboard/presences/suivi_presence_classe.html', context)

@login_required
def suivi_presence_eleve(request, etudiant_id):
    etudiant = get_object_or_404(Etudiant, pk=etudiant_id)
    annee_active = AnneeScolaire.objects.filter(active=True).first()

    # Historique des présences de l'élève
    presences = Presence.objects.filter(
        etudiant=etudiant,
        annee_scolaire=annee_active
    ).order_by('-date')

    # Statistiques de présence pour l'année active
    total_jours_presents = presences.filter(statut='Présent').count()
    total_jours_absents = presences.filter(statut='Absent').count()
    total_jours_retard = presences.filter(statut='Retard').count()
    total_jours_excuses = presences.filter(statut='Excusé').count()

    context = {
        'etudiant': etudiant,
        'presences': presences,
        'total_jours_presents': total_jours_presents,
        'total_jours_absents': total_jours_absents,
        'total_jours_retard': total_jours_retard,
        'total_jours_excuses': total_jours_excuses,
        'annee_active': annee_active,
    }
    return render(request, 'dashboard/presences/suivi_presence_eleve.html', context)

