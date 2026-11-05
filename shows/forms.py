# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django import forms

from .models import WatchEntry


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
