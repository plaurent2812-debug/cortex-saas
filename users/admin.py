from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """
    Configuration de l'administration pour le modèle CustomUser.
    """
    
    # Champs affichés dans la liste
    list_display = ('email', 'first_name', 'last_name', 'is_premium', 'is_staff', 'date_joined')
    list_filter = ('is_premium', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'stripe_customer_id')
    ordering = ('-date_joined',)
    
    # Organisation des champs dans le formulaire de détail
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name')
        }),
        (_('Abonnement & Facturation'), {
            'fields': ('is_premium', 'stripe_customer_id'),
            'classes': ('wide',),
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        (_('Dates importantes'), {
            'fields': ('last_login', 'date_joined', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    # Champs pour l'ajout d'un nouvel utilisateur
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_premium'),
        }),
    )
    
    # Champs en lecture seule
    readonly_fields = ('date_joined', 'updated_at', 'last_login')
    
    # Actions en masse personnalisées
    actions = ['make_premium', 'remove_premium']
    
    @admin.action(description=_("Activer le statut premium pour les utilisateurs sélectionnés"))
    def make_premium(self, request, queryset):
        """Active le statut premium pour les utilisateurs sélectionnés."""
        updated = queryset.update(is_premium=True)
        self.message_user(
            request,
            _(f"{updated} utilisateur(s) ont été passés en premium."),
        )
    
    @admin.action(description=_("Retirer le statut premium des utilisateurs sélectionnés"))
    def remove_premium(self, request, queryset):
        """Retire le statut premium pour les utilisateurs sélectionnés."""
        updated = queryset.update(is_premium=False)
        self.message_user(
            request,
            _(f"{updated} utilisateur(s) ont perdu leur statut premium."),
        )
