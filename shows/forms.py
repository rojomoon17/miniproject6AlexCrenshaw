# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django import forms

from .models import Show, ShowRequest, WatchEntry


class BootstrapFormMixin:
    """Adds Bootstrap's CSS classes to every field's widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs['class'] = css_class


class WatchEntryForm(BootstrapFormMixin, forms.ModelForm):
    """Expects an instance with its user and show already set by the view."""

    class Meta:
        model = WatchEntry
        fields = ['status', 'episodes_watched', 'rating', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        episode_count = self.instance.show.episode_count
        episodes_field = self.fields['episodes_watched']
        episodes_field.widget.attrs.update({'min': 0, 'max': episode_count})
        episodes_field.help_text = (
            f'Out of {episode_count}. Choosing Completed marks every episode as watched.'
        )


class ShowRequestForm(BootstrapFormMixin, forms.ModelForm):
    """Expects an instance with requested_by already set by the view."""

    class Meta:
        model = ShowRequest
        fields = ['title', 'network', 'note']
        widgets = {'note': forms.Textarea(attrs={'rows': 3})}

    def clean_title(self):
        title = self.cleaned_data['title']
        if Show.objects.filter(title__iexact=title).exists():
            raise forms.ValidationError(
                f'{title} is already in the catalog. If you mean a different show with the same name, '
                'add its year or country to the title.'
            )
        if ShowRequest.objects.filter(title__iexact=title, status=ShowRequest.Status.PENDING).exists():
            raise forms.ValidationError(f'{title} has already been requested.')
        return title
