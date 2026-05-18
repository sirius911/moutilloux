from django.contrib.auth.views import LoginView
from django.urls import reverse


class CustomLoginView(LoginView):
    template_name = "registration/login.html"

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return reverse("panel_home")  # adapte si ton URL s'appelle différemment
        if user.groups.filter(name="Arbitre").exists():
            return reverse("referee_home")
        return reverse("results")  # ou une page d'accueil
