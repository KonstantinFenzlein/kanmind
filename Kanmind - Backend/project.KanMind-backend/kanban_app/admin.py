from django.contrib import admin
from .models import Boards, DashboardTasks, Comment
# Hier eigene Models registrieren.

class BoardsAdmin(admin.ModelAdmin):
    # Admin-Oberfläche für das Boards-Model
    # - Zeigt das Feld 'title' in der Listenansicht an
    list_display=["title"]

class DashboardTasksAdmin(admin.ModelAdmin):
    # Admin-Oberfläche für das DashboardTasks-Model
    # - Zeigt das Feld 'title' in der Listenansicht an
    list_display=["title"]

class CommentAdmin(admin.ModelAdmin):
    # Admin-Oberfläche für das Comment-Model
    # - Zeigt das Feld 'content' in der Listenansicht an
    list_display=["content"]

admin.site.register(Boards, BoardsAdmin)
admin.site.register(DashboardTasks, DashboardTasksAdmin)
admin.site.register(Comment, CommentAdmin)
