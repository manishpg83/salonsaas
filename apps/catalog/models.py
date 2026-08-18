from django.db import models

from apps.core.models import SalonScopedModel


class ServiceCategory(SalonScopedModel):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["salon", "name"], name="unique_service_category_name_per_salon"
            ),
        ]

    def __str__(self):
        return self.name


class Service(SalonScopedModel):
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        UNISEX = "UNISEX", "Unisex"

    category = models.ForeignKey(
        ServiceCategory, on_delete=models.CASCADE, related_name="services"
    )
    # Optional: null means "offered at every branch". SET_NULL (not CASCADE)
    # so deleting a branch doesn't delete the services offered there.
    branch = models.ForeignKey(
        "salons.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    duration_minutes = models.PositiveIntegerField()
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.UNISEX)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
