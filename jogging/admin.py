from django.contrib import admin
from jogging.models import Log, LogSummary

class LogAdmin(admin.ModelAdmin):
    date_hierarchy = 'datetime'
    model = Log
    list_display = ['datetime', 'host', 'level', 'source', 'abbrev_msg', 'logs']
    search_fields = ['source', 'msg', 'host']
    list_filter = ['level', 'source', 'host']

class LogSummaryAdmin(admin.ModelAdmin):
    date_hierarchy = 'latest'
    model = LogSummary
    list_display = ['latest', 'earliest', 'hits', 'host', 'level', 'source', 'abbrev_msg', 'summary']
    search_fields = ['source', 'msg', 'host']
    list_filter = ['level', 'source', 'host']

admin.site.register(Log, LogAdmin)
admin.site.register(LogSummary, LogSummaryAdmin)
