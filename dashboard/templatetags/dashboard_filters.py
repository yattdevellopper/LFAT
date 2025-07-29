# dashboard/templatetags/dashboard_filters.py
from django import template

register = template.Library()

@register.filter
def get_edt_item(edt_items, jour_heure_tuple):
    # edt_items est une liste/queryset d'objets EmploiDuTemps
    # jour_heure_tuple est un tuple (jour, heure)
    jour, heure = jour_heure_tuple
    for item in edt_items:
        # Assurez-vous que les types de jour et heure correspondent à vos modèles
        if str(item.jour_semaine) == str(jour) and item.heure_debut.strftime('%H:%M') == heure:
            return item
    return None

# Pour utiliser ce filtre, ajoutez {% load dashboard_filters %} en haut de votre template HTML.