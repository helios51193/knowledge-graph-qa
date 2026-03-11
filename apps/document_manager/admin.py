from django.contrib import admin
from .models import ProcessingLog, Document
class ProcessingLogInline(admin.TabularInline):
    model = ProcessingLog
    extra = 0


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    inlines = [ProcessingLogInline]
