from django.contrib import admin
from .models import Client, Department, Interaction, Document


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Department Information', {
            'fields': ('name', 'prompt')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    search_fields = ('name', 'email')
    filter_horizontal = ('departments',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Client Information', {
            'fields': ('name', 'email', 'password')
        }),
        ('Departments', {
            'fields': ('departments',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'department', 'created_at')
    search_fields = ('client__name', 'department__name', 'title')
    list_filter = ('department', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Interaction Information', {
            'fields': ('client', 'department', 'title')
        }),
        ('Conversation', {
            'fields': ('conversation',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'interaction', 'created_at')
    search_fields = ('file_name', 'interaction__id')
    list_filter = ('created_at', 'file_type')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Document Information', {
            'fields': ('interaction', 'file_name', 'file_type', 'file')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
