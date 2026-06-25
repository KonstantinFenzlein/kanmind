from django.db import models
from django.contrib.auth.models import User

class Boards(models.Model):
    # Repräsentiert ein Kanban-Board.
    # - title: Name des Boards
    # - members: Mit diesem Board verknüpfte Benutzer (ManyToMany)
    # - created_date: Datum, an dem das Board erstellt wurde
    title = models.CharField(max_length=150)
    members = models.ManyToManyField(User, related_name="shared_boards")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="boards_owner", null=False, blank=False)
    created_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title
class DashboardTasks(models.Model):
    # Repräsentiert eine Task im Kanban-System.
    # Felder:
    # - title: Kurzer Titel der Task
    # - description: Ausführliche Beschreibung
    # - board: Zugehöriges Board (nullable)
    # - assignee_id: Benutzer, der die Task erledigen soll
    # - reviewer_id: Benutzer, der die Task überprüft
    # - due_date: Optionale Frist
    # - priority: Priorität der Task (low, medium, high)
    # - status: Status der Task (to-do, in-progress, review, done)
    PRIORITY_CHOICES = [
        ("low", "low priority"),
        ("medium", "medium priority"),
        ("high", "high priority"),
    ]

    STATUS_CHOICES = [
        ("to-do", "to-do"),
        ("in-progress", "in-progress"),
        ("review", "review"),
        ("done", "done"),
    ]

    title = models.CharField(max_length=150)
    description = models.TextField()
    created_by = models.ForeignKey(User, related_name="created_tasks", on_delete=models.SET_NULL, null=True, blank=True)
    board = models.ForeignKey(Boards,related_name="tasks", on_delete=models.SET_NULL, null=True, blank=True)
    assignee_id = models.ForeignKey(User, related_name="assigned_tasks", on_delete=models.SET_NULL, null=True, blank=True)
    reviewer_id = models.ForeignKey(User, related_name="reviewed_tasks", on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=6, choices=PRIORITY_CHOICES, default="medium")
    status =  models.CharField(max_length=15, choices=STATUS_CHOICES, default="to-do")

    def __str__(self):
        return self.title

class Comment(models.Model):
    # Repräsentiert einen Kommentar zu einer Task.
    # Felder:
    # - task: Die zugehörige Task (nullable)
    # - content: Text des Kommentars (max. 300 Zeichen)
    # - created_at: Zeitstempel der Erstellung des Kommentars
    # - author: Benutzer, der den Kommentar geschrieben hat
    task = models.ForeignKey(DashboardTasks, related_name="comments", null=True, blank=True, on_delete=models.SET_NULL)
    content = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.content[:50]
