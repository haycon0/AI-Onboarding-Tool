from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class Department(models.Model):
    """
    Department model representing organizational departments.
    Associated with multiple lawyers and clients.
    """
    name = models.CharField(max_length=255, unique=True)
    prompt = models.TextField(
        help_text="Associated AI prompt for this department"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Client(models.Model):
    """
    Client model representing clients in the system.
    Has many interactions and potentially multiple departments.
    """
    name = models.CharField(max_length=255)
    email = models.EmailField()
    password = models.CharField(max_length=255)
    departments = models.ManyToManyField(
        Department,
        related_name='clients',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Interaction(models.Model):
    """
    Interaction model storing AI discussion between a client and the system.
    Associated with a client and a department, can contain multiple documents.
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='interactions',
        null=True,
        blank=True
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='interactions',
        null=True,
        blank=True,
    )
    
    title = models.CharField(max_length=255, blank=True)
    system_instructions = models.TextField(
        blank=True,
        default="",
        help_text="System instructions used to initialize the interaction"
    )
    conversation = models.JSONField(
        default=list,
        help_text="Stores the entire AI discussion as JSON array"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        client_name = self.client.name if self.client else "No Client"
        return f"{client_name} - {self.department.name}"

    class Meta:
        ordering = ['-created_at']


class Document(models.Model):
    """
    Document model representing files/documents associated with interactions.
    """
    interaction = models.ForeignKey(
        Interaction,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='interaction_documents/%Y/%m/%d/')
    file_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_name} ({self.interaction.id})"

    class Meta:
        ordering = ['-created_at']
