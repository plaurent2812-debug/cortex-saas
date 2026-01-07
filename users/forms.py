from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """
    Formulaire d'inscription personnalisé pour CustomUser.
    Utilise l'email au lieu du username.
    """
    
    email = forms.EmailField(
        label='Adresse email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'votre@email.com'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ('email',)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnaliser les champs de mot de passe
        self.fields['password1'].widget.attrs.update({
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Mot de passe'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Confirmer le mot de passe'
        })


class CustomUserChangeForm(UserChangeForm):
    """
    Formulaire de modification d'utilisateur pour l'admin.
    """
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'is_premium')
