from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrMemberBoard(BasePermission):
    
    # Objekt-bezogene Berechtigung für den Board-Zugriff.
    # - Der Benutzer muss authentifiziert sein (wird durch IsAuthenticated geprüft)
    # - Der Benutzer muss Besitzer oder Mitglied des Boards sein
    

    def has_permission(self, request, view):
        # Nur authentifizierten Benutzern den Zugriff erlauben.
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Objekt-bezogene Prüfung NACHDEM das Board geladen wurde (404 bereits behandelt)
        user = request.user
        return obj.owner == user or user in obj.members.all()

class IsBoardMemberForTask(BasePermission):
    # Nur der Board-Besitzer oder Board-Mitglieder dürfen auf die Task zugreifen
    def has_permission(self, request, view):
        # Nur authentifizierten Benutzern den Zugriff erlauben.
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not obj.board:
            return False  
        user = request.user
        if request.method == "DELETE":
            return obj.board.owner == user or obj.created_by == user

        return obj.board.owner == user or user in obj.board.members.all() 

class IsCommentAuthorOrBoardMember(BasePermission):
    
    # - GET → Board-Mitglieder oder Besitzer
    # - POST → Board-Mitglieder oder Besitzer
    # - PUT/PATCH, DELETE → nur der Kommentar-Ersteller

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        # GET/POST → Board-Mitglieder oder Besitzer
        if request.method in SAFE_METHODS:
            if not obj.task or not obj.task.board:
                return False  # Task oder Board fehlt → verweigern
            board = obj.task.board
            return user == board.owner or user in board.members.all()

        # Bearbeiten/Löschen → nur der Kommentar-Ersteller
        return user == obj.author