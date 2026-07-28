"""
URL configuration for moutilloux project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.views.static import serve
from live.auth_views import CustomLoginView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # L'admin Django natif (configuration initiale) vit sous `/django-admin/` :
    # `/admin/` est réservé aux écrans d'administration de la SPA Vue, qui
    # partagent désormais le même port.
    path('django-admin/', admin.site.urls),
    path("", include("live.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/login/", CustomLoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# `serve` explicite (et non le helper `static()`, désactivé hors DEBUG) pour que
# les photos de joueurs et les affiches restent servies en réseau local.
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]

# ── SPA Vue (build de production) ──────────────────────────────────────
# Sert `frontend/app/dist/` pour un usage en réseau local sans dev server
# Vite. Sans build présent, ces routes renvoient 404 / TemplateDoesNotExist
# et le mode dev (Vite :5173 + proxy) reste inchangé.
urlpatterns += [
    # bundles hashés générés par Vite
    re_path(
        r"^assets/(?P<path>.*)$",
        serve,
        {"document_root": settings.SPA_DIST_DIR / "assets"},
    ),
    # fichiers déposés à la racine de `public/` (favicon, manifest, icônes…)
    re_path(
        r"^(?P<path>[\w.-]+\.(?:svg|png|ico|webmanifest|json|txt))$",
        serve,
        {"document_root": settings.SPA_DIST_DIR},
    ),
    # history mode : toute autre URL rend index.html, le routeur Vue prend le relais
    re_path(
        r"^(?!api/|django-admin/|accounts/|media/|static/).*$",
        TemplateView.as_view(template_name="index.html"),
        name="spa",
    ),
]
