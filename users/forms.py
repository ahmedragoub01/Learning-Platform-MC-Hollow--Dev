# forms.py
from django import forms

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match")
        
        return cleaned_data

from django import forms
from .models import Topic, Post

class NewTopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title']

class NewPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['message']



