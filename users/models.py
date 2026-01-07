from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Manager personnalisé pour CustomUser qui utilise l'email au lieu du username.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Crée et sauvegarde un utilisateur avec l'email et le mot de passe donnés.
        """
        if not email:
            raise ValueError(_('L\'adresse email est obligatoire'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crée et sauvegarde un superutilisateur avec l'email et le mot de passe donnés.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Modèle utilisateur personnalisé qui utilise l'email comme identifiant unique
    au lieu du username. Inclut les champs pour la gestion premium et Stripe.
    """
    
    # Supprimer le champ username
    username = None
    
    # Email comme identifiant unique
    email = models.EmailField(_('adresse email'), unique=True)
    
    # Champs pour le modèle SaaS
    is_premium = models.BooleanField(
        _('statut premium'),
        default=False,
        help_text=_('Indique si l\'utilisateur a un abonnement premium actif.')
    )
    
    stripe_customer_id = models.CharField(
        _('ID client Stripe'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Identifiant du client dans Stripe pour gérer les paiements.')
    )
    
    # Champs supplémentaires optionnels
    date_joined = models.DateTimeField(_('date d\'inscription'), auto_now_add=True)
    updated_at = models.DateTimeField(_('dernière modification'), auto_now=True)
    
    # Configuration
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email est déjà requis par défaut
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """
        Retourne le nom complet de l'utilisateur.
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email
    
    def get_short_name(self):
        """
        Retourne le prénom de l'utilisateur ou l'email si non défini.
        """
        return self.first_name or self.email.split('@')[0]
