from django import forms
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'dateofbirth', 'phone', 'email', 'profile_picture', 'resume', 'skills']

        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'resume': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your skills separated by commas (e.g., ReactJS, Python, Django)'
            }),
            'dateofbirth': forms.DateInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your date of birth'
            })
        }

        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'phone': 'Phone Number',
            'email': 'Email Address',
            'profile_picture': 'Profile Picture',
            'resume': 'Resume',
            'skills': 'Skills',
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone

    def clean_skills(self):
        skills = self.cleaned_data.get('skills')
        if skills:
            # Clean up the skills string
            skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
            return ', '.join(skills_list)
        return skills