from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    # Customize the widgets for the fields
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control mb-3'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control mb-3'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control mb-3'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control mb-3'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control mb-3'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control mb-3'}))


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    # Customize the widgets for the fields
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control mb-3'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control mb-3'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control mb-3'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control mb-3'}))


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control mb-3'}))

    def clean_username(self):
        username = self.cleaned_data.get('username')

        # Check if the input is an email address
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                return user.username  # Return the username for authentication
            except User.DoesNotExist:
                raise forms.ValidationError("No user with this email found.")
        return username


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('profile_picture',)
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control-file mb-3'}),
        }


from django import forms
from .models import NewsArticle

class NewsArticleForm(forms.ModelForm):
    class Meta:
        model = NewsArticle
        fields = ('title', 'content')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Enter news content here...'}),
        }
