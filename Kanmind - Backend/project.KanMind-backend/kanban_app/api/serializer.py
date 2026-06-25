from django.contrib.auth.models import User
from rest_framework import serializers
from kanban_app.models import Boards, DashboardTasks, Comment

# Serializer für die Basis-Benutzerdaten (id, username, email, Vor- und Nachname).
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]

# Serializer zur Darstellung eines Benutzers mit ID, E-Mail und vollständigem Namen.
class CheckMailSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id' ,'email','fullname']
    # Setzt den vollständigen Namen aus Vor- und Nachname zusammen.
    def get_fullname(self, obj):
        return obj.get_full_name()

# Serializer für das DashboardTasks-Model inkl. Assignee/Reviewer und Kommentaranzahl.
class TasksSerializer(serializers.ModelSerializer):
    reviewer = CheckMailSerializer(source="reviewer_id", read_only=True)
    assignee = CheckMailSerializer(source="assignee_id", read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    board = serializers.PrimaryKeyRelatedField(queryset=Boards.objects.all())
    comments_count = serializers.SerializerMethodField()


    # Zählt die Kommentare der Task.
    def get_comments_count(self, obj):
        return obj.comments.count()

    # Prüft, dass Assignee und Reviewer Mitglieder des zugehörigen Boards sind.
    def validate(self, attrs):
        board = attrs.get("board") or getattr(self.instance, "board", None)
        assignee = attrs.get("assignee_id")
        reviewer = attrs.get("reviewer_id")

        if board:
            board_members = board.members.all()
            invalid_users = []

            if assignee and assignee not in board_members:
                invalid_users.append("assignee_id")
            if reviewer and reviewer not in board_members:
                invalid_users.append("reviewer_id")

            if invalid_users:
                raise serializers.ValidationError(
                    {field: "User must be a member of the board." for field in invalid_users}
                )

        return attrs

    class Meta:
        model = DashboardTasks
        fields = ['id' ,'board' ,'title','description','status', 'priority','assignee', 'assignee_id', 'reviewer', 'reviewer_id', 'due_date', 'comments_count']

# Serializer für die Detailansicht einer einzelnen Task (ohne Board-Feld).
class TaskDetailSerializer(serializers.ModelSerializer):

    reviewer = CheckMailSerializer(source="reviewer_id", read_only=True)
    assignee = CheckMailSerializer(source="assignee_id", read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = DashboardTasks
        fields = ['id' ,'title','description','status', 'priority','assignee', 'assignee_id', 'reviewer', 'reviewer_id', 'due_date']

    # Prüft, dass Assignee und Reviewer Mitglieder des zugehörigen Boards sind.
    def validate(self, attrs):
        board = getattr(self.instance, "board", None)
        assignee = attrs.get("assignee_id")
        reviewer = attrs.get("reviewer_id")

        if board:
            board_members = board.members.all()
            invalid_users = []

            if assignee and assignee not in board_members:
                invalid_users.append("assignee_id")
            if reviewer and reviewer not in board_members:
                invalid_users.append("reviewer_id")

            if invalid_users:
                raise serializers.ValidationError(
                    {field: "User must be a member of the board." for field in invalid_users}
                )

        return attrs

# Mixin mit zusätzlichen Kennzahl-Feldern für ein Board (Mitglieder-, Ticket- und Task-Zählungen).
class BoardsMixin(serializers.Serializer):
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    # Zählt die Mitglieder des Boards.
    def get_member_count(self, obj):
        return obj.members.count()

    # Zählt alle Tasks des Boards.
    def get_ticket_count(self, obj):
        return obj.tasks.count()

    # Zählt die Tasks des Boards mit Status 'to-do'.
    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status="to-do").count()

    # Zählt die Tasks des Boards mit hoher Priorität.
    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(priority="high").count()

# Mixin, das die Owner-ID eines Boards als Lesefeld bereitstellt.
class OwnerIdMixin(serializers.Serializer):
    owner_id = serializers.ReadOnlyField(source="owner.id")

# Serializer für die Listenansicht eines Boards inkl. Kennzahlen und Owner-ID.
class BoardsSerializer(BoardsMixin,OwnerIdMixin, serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        write_only=True
    )

    class Meta:
        model = Boards
        fields = ['id' ,'title', 'member_count', 'ticket_count', 'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id', 'members']


# Serializer für die Detailansicht eines Boards mit Owner-, Mitglieder- und Task-Daten.
class BoardDetailSerializer(OwnerIdMixin, serializers.ModelSerializer):



    owner_data = CheckMailSerializer(source="owner", read_only=True)
    members_data = CheckMailSerializer(source="members", many=True, read_only=True)
    members = CheckMailSerializer(many=True, read_only=True)
    members_ids = serializers.PrimaryKeyRelatedField(
        source="members",
        many=True,
        queryset=User.objects.all(),
        write_only=True
    )

    tasks = TasksSerializer(many=True,read_only=True)
    class Meta:
        model = Boards
        fields = ['id' ,'title','owner_id', 'members', 'owner_data','members_data', 'members_ids', 'tasks']

    # Entfernt je nach Request-Methode (PATCH/GET) die jeweils nicht benötigten Felder.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")

        if request:
            if request.method == "PATCH":
                # Felder für PATCH-Requests entfernen
                self.fields.pop("owner_id", None)
                self.fields.pop("members", None)
                self.fields.pop("tasks", None)
            elif request.method == "GET":
                # Felder für GET-Requests entfernen
                self.fields.pop("owner_data", None)
                self.fields.pop("members_data", None)
                self.fields.pop("members_ids", None)

    # Mappt das Eingabefeld 'members' auf 'members_ids', bevor die Validierung läuft.
    def to_internal_value(self, data):
        data = data.copy()
        # members_ids in members schreiben
        if 'members' in data and 'members_ids' not in data:
            data['members_ids'] = data.pop('members')
        return super().to_internal_value(data)

# Serializer für das Comment-Model mit dem vollständigen Namen des Autors.
class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(
        source='author.get_full_name',
        read_only=True
    )
    class Meta:
        model = Comment
        fields = ['id','created_at', 'author', 'content']
        read_only_fields = ['created_at', 'author']
