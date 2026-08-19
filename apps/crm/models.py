from django.db import models

from apps.core.models import SalonScopedModel


class Customer(SalonScopedModel):
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    class Source(models.TextChoices):
        WALK_IN = "WALK_IN", "Walk-in"
        REFERRAL = "REFERRAL", "Referral"
        INSTAGRAM = "INSTAGRAM", "Instagram"
        FACEBOOK = "FACEBOOK", "Facebook"
        GOOGLE = "GOOGLE", "Google"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        OTHER = "OTHER", "Other"

    name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    dob = models.DateField(null=True, blank=True)
    anniversary = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=20, choices=Source.choices, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["salon", "mobile"], name="unique_customer_mobile_per_salon"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.mobile})"
