from django import forms
from .models import NDEReport


class NDEReportUploadForm(forms.ModelForm):
    class Meta:
        model = NDEReport
        fields = ['title', 'report_type', 'section', 'report_file', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MT Report TVA AX-1 thru AX-24.5'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. AX, CX (optional)'}),
            'report_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional: keywords, summary, inspector name, weld range...'}),
        }
        labels = {
            'report_file': 'PDF File',
            'notes': 'Notes / Keywords (for searching)',
        }
