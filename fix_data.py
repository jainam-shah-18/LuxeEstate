import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LuxeEstate.settings")
django.setup()

from properties.models import Property, PropertyImage

indoor = {'kitchen', 'modular kitchen', 'open kitchen', 'closed kitchen', 'bedroom', 'bathroom', 'living room'}
outdoor = {'swimming pool', 'garden', 'parking space'}

changed = 0
for img in PropertyImage.objects.all():
    if not img.ai_detected_features: continue
    
    features = set(img.ai_detected_features)
    has_indoor = features.intersection(indoor)
    has_outdoor = features.intersection(outdoor)
    
    # If both indoor and outdoor are present, it's likely a hallucination.
    # Usually, if it's explicitly a kitchen/bedroom/living room, the pool/garden is false.
    # We will remove outdoor features if any indoor feature is present, as indoor is more defining.
    if has_indoor and has_outdoor:
        original = list(features)
        features = features - outdoor
        img.ai_detected_features = list(features)
        img.save(update_fields=['ai_detected_features'])
        print(f"Fixed image {img.id}: {original} -> {img.ai_detected_features}")
        changed += 1

print(f"Fixed {changed} images.")

# Now clean up Property ai_tags which may have aggregated the bad features.
for prop in Property.objects.all():
    image_features = set()
    for img in prop.images.all():
        if img.ai_detected_features:
            image_features.update(img.ai_detected_features)
    
    # We should merge image_features back into ai_tags, but we might want to just keep ai_tags clean
    # from hallucinated ones.
    if prop.ai_tags:
        tags = set(prop.ai_tags)
        # If the property's images no longer have the outdoor feature, and it was in ai_tags,
        # it might have originated from the image hallucination.
        # But we won't touch ai_tags unless it's strictly necessary.
        pass
