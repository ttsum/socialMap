from django.urls import path
from .views import ActivityDetailView, ActivityListView, RecommendationView, MembershipView, FavoriteView, GroupMessagesView, MeGroupsView, MeFavoritesView, ConversationsView, PublishRequestView

urlpatterns = [
    path('activities/', ActivityListView.as_view()),
    path('activities/<str:activity_id>/', ActivityDetailView.as_view()),
    path('recommendations/', RecommendationView.as_view()),
    path('groups/<str:group_id>/membership/', MembershipView.as_view()),
    path('activities/<str:activity_id>/favorite/', FavoriteView.as_view()),
    path('groups/<str:group_id>/messages/', GroupMessagesView.as_view()),
    path('me/groups/', MeGroupsView.as_view()),
    path('me/favorites/', MeFavoritesView.as_view()),
    path('conversations/', ConversationsView.as_view()),
    path('publish-requests/', PublishRequestView.as_view()),
]
