from django.urls import path
from .views import  (
    BoardView, 
    ReviewerTaskView, 
    TaskView, 
    UserEmailList, 
    BoardSingleView, 
    TasksSingleView, 
    AssignedTaskView, 
    TaskCommentsView, 
    CommentSingleView
)

# API-Endpunkte zur Verwaltung von Benutzern, Boards, Tasks und Kommentaren

urlpatterns = [
    path('email-check/', UserEmailList.as_view(), name='email-check'),
    path('boards/', BoardView.as_view(), name='board'),
    path('boards/<int:board_id>/', BoardSingleView.as_view(), name='board-single-view'),
    path('tasks/', TaskView.as_view(), name='taskview'),
    path('tasks/assigned-to-me/', AssignedTaskView.as_view(), name='assigned-task'),
    path('tasks/reviewing/', ReviewerTaskView.as_view(), name='reviewing'),
    path('tasks/<int:task_id>/', TasksSingleView.as_view(), name='tasksSingleview'),
    path('tasks/<int:task_pk>/comments/', TaskCommentsView.as_view(), name='task-comments'),
    path('tasks/<int:task_pk>/comments/<int:pk>/', CommentSingleView.as_view(), name='task-single-comments'),
]