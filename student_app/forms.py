from django import forms
from django.core.validators import FileExtensionValidator
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Subject, ContributorRequest, ContactMessage, UserProfile
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Button, HTML
from crispy_forms.bootstrap import PrependedText, PrependedAppendedText
from .models import Faculty

class ContributeResourceForm(forms.Form):
    RESOURCE_TYPES = [
        ('note', 'Note'),
        ('syllabus', 'Syllabus'),
        ('questionbank', 'Question Bank'),
    ]
    resource_type = forms.ChoiceField(choices=RESOURCE_TYPES, label='Resource Type')
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.filter(is_active=True), 
        label='Faculty',
        empty_label="Select Faculty"
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(), 
        label='Subject',
        empty_label="Select Subject (choose faculty first)"
    )
    title = forms.CharField(max_length=200, label='Title')
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False, label='Description')
    file = forms.FileField(
        label='File',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx'])],
        help_text='Supported formats: PDF, DOC, DOCX, TXT, PPT, PPTX (Max 10MB)'
    )
    tags = forms.CharField(
        max_length=200, 
        required=False, 
        label='Tags',
        help_text='Separate tags with commas (e.g., exam, important, chapter1)'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial faculty if user has one assigned
        if 'initial' not in kwargs:
            self.fields['subject'].queryset = Subject.objects.filter(is_active=True, faculty__isnull=False)

    def clean(self):
        cleaned_data = super().clean()
        faculty = cleaned_data.get('faculty')
        subject = cleaned_data.get('subject')
        
        if faculty and subject:
            if subject.faculty != faculty:
                raise forms.ValidationError("Selected subject does not belong to the selected faculty.")
        
        return cleaned_data

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError("File size must be under 10MB.")
        return file


class ContributorRequestForm(forms.ModelForm):
    class Meta:
        model = ContributorRequest
        fields = ['faculty', 'reason', 'experience']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Why do you want to become a contributor?'}),
            'experience': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe your relevant experience (optional)'}),
        }
        labels = {
            'faculty': 'Faculty/Department',
            'reason': 'Reason for Request',
            'experience': 'Relevant Experience',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['faculty'].queryset = self.fields['faculty'].queryset.filter(is_active=True)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.layout = Layout(
            'faculty',
            'reason',
            'experience',
            Submit('submit', 'Submit Request', css_class='btn btn-primary')
        )


class EnhancedContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'your.email@example.com'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Subject of your message'}),
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Your message here...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6'),
                Column('email', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            'subject',
            'message',
            Submit('submit', 'Send Message', css_class='btn btn-primary')
        )


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.filter(is_active=True),
        required=False,
        empty_label="Select Faculty (Optional)"
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide password help text to avoid duplication
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        
        # Add placeholders and styling
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = UserProfile
        fields = ['faculty', 'bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['faculty'].queryset = self.fields['faculty'].queryset.filter(is_active=True)
        
        # Set initial values for user fields
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        
        # Add CSS classes to form fields
        for field_name, field in self.fields.items():
            if field_name in ['first_name', 'last_name', 'email']:
                field.widget.attrs.update({'class': 'form-control'})
            elif field_name == 'faculty':
                field.widget.attrs.update({'class': 'form-select'})
            elif field_name == 'bio':
                field.widget.attrs.update({'class': 'form-control'})
            elif field_name == 'avatar':
                field.widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.instance and self.instance.user:
            # Check if email is being changed and if it's already taken
            if email != self.instance.user.email and User.objects.filter(email=email).exists():
                raise forms.ValidationError("This email address is already registered.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        if commit:
            # Update user fields
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            
            # Save profile
            profile.save()
        
        return profile


class AdminResponseForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['status', 'admin_response']
        widgets = {
            'admin_response': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Your response to the user...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'status',
            'admin_response',
            Submit('submit', 'Send Response', css_class='btn btn-primary')
        )


class ResourceFilterForm(forms.Form):
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.filter(is_active=True),
        required=False,
        empty_label="All Faculties"
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.filter(is_active=True),
        required=False,
        empty_label="All Subjects"
    )
    resource_type = forms.ChoiceField(
        choices=[('', 'All Types'), ('note', 'Notes'), ('syllabus', 'Syllabus'), ('questionbank', 'Question Banks')],
        required=False
    )
    level = forms.ChoiceField(
        choices=[('', 'All Levels')] + [(i, f'Level {i}') for i in range(1, 9)],
        required=False
    )
    tags = forms.CharField(max_length=200, required=False, help_text='Search by tags')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Faculty and Subject querysets are already set correctly
        self.fields['subject'].queryset = Subject.objects.filter(is_active=True, faculty__isnull=False)


class AdvancedSearchForm(forms.Form):
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search for resources...'})
    )
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.none(),
        required=False,
        empty_label="All Faculties"
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(),
        required=False,
        empty_label="All Subjects"
    )
    resource_type = forms.MultipleChoiceField(
        choices=[('note', 'Notes'), ('syllabus', 'Syllabus'), ('questionbank', 'Question Banks')],
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    level = forms.MultipleChoiceField(
        choices=[(i, f'Level {i}') for i in range(1, 9)],
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('relevance', 'Relevance'),
            ('newest', 'Newest First'),
            ('oldest', 'Oldest First'),
            ('downloads', 'Most Downloaded'),
            ('views', 'Most Viewed')
        ],
        initial='relevance',
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Faculty
        self.fields['faculty'].queryset = Faculty.objects.filter(is_active=True)
        self.fields['subject'].queryset = Subject.objects.filter(is_active=True, faculty__isnull=False) 