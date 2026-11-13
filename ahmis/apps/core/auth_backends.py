from django.conf import settings
from django.contrib.auth.backends import ModelBackend


class LocalBackend(ModelBackend):
    """Comptes locaux AHMIS (mot de passe stocké dans la base).

    Avec AHMIS_LOCAL_LOGIN=0, seuls les superutilisateurs locaux peuvent encore se connecter
    par mot de passe : c'est le compte de secours si l'annuaire d'entreprise est indisponible.
    """

    def user_can_authenticate(self, user):
        if not super().user_can_authenticate(user):
            return False
        if not settings.AHMIS_AUTH["LOCAL_LOGIN"] and not user.is_superuser:
            return False
        return True
