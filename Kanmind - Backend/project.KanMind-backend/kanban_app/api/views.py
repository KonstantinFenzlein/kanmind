from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.core.validators import validate_email
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.db.models import Q
from rest_framework import status, generics, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateDestroyAPIView, GenericAPIView, ListCreateAPIView
from rest_framework.exceptions import NotFound
from kanban_app.models import Boards, Comment, DashboardTasks
from .serializer import BoardDetailSerializer, BoardsSerializer, CheckMailSerializer, TaskDetailSerializer, TasksSerializer, CommentSerializer
from auth_app.api.permissions import IsBoardMemberForTask, IsOwnerOrMemberBoard, IsCommentAuthorOrBoardMember

class UserEmailList(APIView):
    # API-Endpunkt zum Abrufen eines Benutzers anhand der E-Mail-Adresse.
    # - GET-Request mit 'email' als Query-Parameter
    # - Gibt den ersten passenden Benutzer mit CheckMailSerializer zurück
    permission_classes = [IsAuthenticated]

    def get(self, request):
        email = request.query_params.get("email")
        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            validate_email(email)
        except ValidationError:
                return Response(
                {"detail": "Invalid email format."},
                status=status.HTTP_400_BAD_REQUEST
            )
        users = User.objects.filter(email=email).first()
        if not users:
            return Response(
                {"detail": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = CheckMailSerializer(users)
        return Response(serializer.data)

class BoardView(ListCreateAPIView):
    # API-Endpunkt zum Auflisten aller Boards mit Kennzahlen oder zum Erstellen eines neuen Boards.
    # GET:
    # - Gibt eine Liste der Boards mit Mitgliederanzahl, Ticketanzahl, Anzahl der zu erledigenden Tasks und Anzahl der Tasks mit hoher Priorität zurück
    # POST:
    # - Erstellt ein neues Board für den authentifizierten Benutzer
    # - Verwendet den authentifizierten Benutzer als Owner und fügt diesen automatisch als Mitglied hinzu
    serializer_class = BoardsSerializer
    permission_classes = [IsAuthenticated]
    queryset = Boards.objects.all()
    def get_queryset(self):
        user = self.request.user
        return Boards.objects.filter(Q(owner=user) | Q(members=user)).distinct()
    def perform_create(self, serializer):
        board = serializer.save(owner=self.request.user)
        board.members.add(self.request.user)

class BoardSingleView(RetrieveUpdateDestroyAPIView):
    # API-Endpunkt für ein einzelnes Board.
    # - Unterstützt GET, PUT/PATCH, DELETE
    # - PATCH aktualisiert Titel und Mitglieder des Boards; Tasks werden über die Task-Endpunkte verwaltet
    # - DELETE ist nur dem Board-Owner erlaubt und entfernt zugehörige Tasks und Kommentare
    queryset = Boards.objects.all()
    serializer_class = BoardDetailSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrMemberBoard]
    lookup_url_kwarg = "board_id"

    def get_object(self):
        # Zuerst prüfen, ob das Board existiert → 404
        # Danach übernimmt DRF automatisch die Berechtigungsprüfung
        obj = super().get_object()
        return obj

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise PermissionDenied("Only the board owner can delete this board.")

        with transaction.atomic():
            related_tasks = list(instance.tasks.all())
            for task in related_tasks:
                task.comments.all().delete()
            for task in related_tasks:
                task.delete()

            instance.delete()

class TaskView(mixins.ListModelMixin, mixins.CreateModelMixin, GenericAPIView):
    # API-Endpunkt zum Auflisten aller Tasks oder zum Erstellen einer neuen Task.
    # GET: Gibt alle Tasks zurück
    # POST: Erstellt eine neue Task
    queryset = DashboardTasks.objects.all()
    serializer_class = TasksSerializer
    permission_classes = [IsBoardMemberForTask]

    def post(self, request, *args, **kwargs):
        board_id = request.data.get("board")

        # Prüfen, ob das Board existiert → 404, falls nicht gefunden
        try:
            board = Boards.objects.get(pk=board_id)
        except Boards.DoesNotExist:
            raise NotFound("Board does not exist.")
        user = request.user
        if board.owner != user and user not in board.members.all():
            raise PermissionDenied("User must be a member of the board to perform this action.")

        # Daten serialisieren und die neue Task speichern
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(board=board, created_by=user)
        return Response(serializer.data, status=201)


class TasksSingleView(RetrieveUpdateDestroyAPIView):
    # API-Endpunkt für eine einzelne Task.
    # - Unterstützt GET, PUT/PATCH, DELETE
    # - PATCH/PUT aktualisiert nur die Task-Felder; die Board-Zuordnung bleibt unverändert
    queryset = DashboardTasks.objects.all()
    permission_classes = [IsBoardMemberForTask]
    serializer_class = TaskDetailSerializer
    lookup_url_kwarg = "task_id"


class AssignedTaskView(APIView):
    # API-Endpunkt zum Abrufen aller Tasks, die dem anfragenden Benutzer zugewiesen sind.
    # - GET-Request
    permission_classes = [IsAuthenticated]
    def get(self, request):
        tasks = DashboardTasks.objects.filter(assignee_id=request.user)
        serializer = TasksSerializer(tasks, many=True)
        return Response(serializer.data)

class ReviewerTaskView(APIView):
    # API-Endpunkt zum Abrufen aller Tasks, bei denen der anfragende Benutzer Reviewer ist.
    # - GET-Request
    permission_classes = [IsAuthenticated]
    def get(self, request):
        tasks = DashboardTasks.objects.filter(reviewer_id=request.user)
        serializer = TasksSerializer(tasks, many=True)
        return Response(serializer.data)

class TaskCommentsView(APIView):
    # API-Endpunkt zum Auflisten oder Erstellen von Kommentaren zu einer bestimmten Task.
    # GET:
    # - Gibt alle Kommentare zur Task zurück
    permission_classes = [IsAuthenticated, IsCommentAuthorOrBoardMember]
    def get(self, request, task_pk):
        task = get_object_or_404(DashboardTasks, pk=task_pk)
        if not task.board:
            raise PermissionDenied("Task is not assigned to a board.")

        user = request.user
        board = task.board
        if user != board.owner and user not in board.members.all():
            raise PermissionDenied("User must be a member of the board to view comments.")

        comments = Comment.objects.filter(task=task).order_by("created_at")
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    # POST:
    # - Erstellt einen neuen Kommentar, verknüpft mit der Task und dem aktuellen Benutzer
    #   URL-Parameter:
    # - task_pk (int): Der Primärschlüssel der Task, mit der der Kommentar verknüpft wird.
    # - Speichert den Kommentar und verknüpft ihn mit:
    #   • task = die abgerufene Task
    #   • author = aktueller Benutzer
    def post(self, request, task_pk):
        task = get_object_or_404(DashboardTasks, pk=task_pk)

        # Prüfen, ob die Task einem Board zugeordnet ist
        if not task.board:
            raise PermissionDenied("Task is not assigned to a board.")

        board = task.board
        user = request.user

        # Nur Board-Owner oder Mitglieder dürfen posten
        if user != board.owner and user not in board.members.all():
            raise PermissionDenied("User must be a member of the board to comment.")

        # Den Kommentar erstellen
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(task=task, author=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CommentSingleView(generics.RetrieveUpdateDestroyAPIView):
    # API-Endpunkt für einen einzelnen Kommentar.
    # - Nur der Ersteller oder ein Superuser darf aktualisieren/löschen
    # - GET-Request für alle verfügbar
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsCommentAuthorOrBoardMember]

    def get_queryset(self):
        # Kommentare nach der jeweiligen Task und dem einzelnen Kommentar filtern
        task_pk = self.kwargs['task_pk']
        return Comment.objects.filter(task_id=task_pk)
