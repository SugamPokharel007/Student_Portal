from django import template
from django.urls import reverse

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0 

@register.filter
def class_name(obj):
    """Get the class name of an object"""
    return obj.__class__.__name__

@register.filter
def get_resource_url(resource):
    """Get the appropriate URL for a resource"""
    if not resource or not hasattr(resource, 'subject') or not resource.subject:
        return '#'
    
    subject_id = resource.subject.id
    
    # Determine resource type and return appropriate URL
    if hasattr(resource, 'resource_type'):
        resource_type = resource.resource_type
    else:
        # Fallback to class name detection
        class_name = resource.__class__.__name__.lower()
        if 'syllabus' in class_name:
            resource_type = 'syllabus'
        elif 'note' in class_name:
            resource_type = 'note'
        elif 'question' in class_name:
            resource_type = 'questionbank'
        else:
            resource_type = 'unknown'
    
    try:
        if resource_type == 'syllabus':
            return reverse('syllabus_detail', kwargs={'subject_id': subject_id, 'syllabus_id': resource.id})
        elif resource_type == 'note':
            return reverse('subject_notes', kwargs={'subject_id': subject_id})
        elif resource_type == 'questionbank':
            return reverse('question_bank_detail', kwargs={'subject_id': subject_id, 'question_bank_id': resource.id})
        else:
            return reverse('subject_detail', kwargs={'subject_id': subject_id})
    except:
        return reverse('subject_detail', kwargs={'subject_id': subject_id})

@register.filter
def get_resource_type_label(resource):
    """Get the type label for a resource"""
    if hasattr(resource, 'resource_type'):
        resource_type = resource.resource_type
    else:
        class_name = resource.__class__.__name__.lower()
        if 'syllabus' in class_name:
            resource_type = 'syllabus'
        elif 'note' in class_name:
            resource_type = 'note'
        elif 'question' in class_name:
            resource_type = 'questionbank'
        else:
            resource_type = 'unknown'
    
    type_labels = {
        'syllabus': 'Syllabus',
        'note': 'Study Notes',
        'questionbank': 'Question Bank',
        'unknown': 'Resource'
    }
    return type_labels.get(resource_type, 'Resource')

@register.filter
def get_resource_icon(resource):
    """Get the icon class for a resource"""
    if hasattr(resource, 'resource_type'):
        resource_type = resource.resource_type
    else:
        class_name = resource.__class__.__name__.lower()
        if 'syllabus' in class_name:
            resource_type = 'syllabus'
        elif 'note' in class_name:
            resource_type = 'note'
        elif 'question' in class_name:
            resource_type = 'questionbank'
        else:
            resource_type = 'unknown'
    
    icon_map = {
        'syllabus': 'fas fa-book',
        'note': 'fas fa-file-alt',
        'questionbank': 'fas fa-question-circle',
        'unknown': 'fas fa-file'
    }
    return icon_map.get(resource_type, 'fas fa-file') 