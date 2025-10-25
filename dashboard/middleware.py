from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class CheckEcoleSubscriptionMiddleware:
    """
    Vérifie si l'école a une période d'essai active ou un abonnement valide.
    Bloque l'accès au système si la période d'essai est expirée et non payée.
    Compatible avec le site d'administration Django.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ⚙️ On ne bloque pas :
        # - les pages d'administration
        # - les pages de connexion / déconnexion
        # - la page de paiement
        exempt_paths = [
            reverse('login'),
            reverse('logout'),
            reverse('initier_paiement'),
            '/admin/login/',
            '/admin/',
        ]

        # ✅ Continuer normalement pour les pages exemptées
        if any(request.path.startswith(path) for path in exempt_paths):
            return self.get_response(request)

        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            ecole = getattr(profile, 'ecole', None)

            if ecole:
                # Si la période d'essai est expirée et que l'école n'a pas payé
                if hasattr(ecole, 'periode_essai_expiree') and ecole.periode_essai_expiree() and not ecole.est_active:
                    messages.warning(
                        request,
                        "⛔ Votre période d'essai gratuite est terminée. "
                        "Veuillez effectuer le paiement pour continuer à utiliser le système."
                    )
                    return redirect('initier_paiement')

        # ✅ Sinon, continuer la requête normalement
        response = self.get_response(request)
        return response
