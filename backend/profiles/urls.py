from django.urls import path

from . import views

urlpatterns = [
    path("areas/", views.AreaListView.as_view(), name="area-list"),
    path("tutors/", views.TutorSearchView.as_view(), name="tutor-search"),
    path("tutors/<int:pk>/", views.TutorDetailView.as_view(), name="tutor-detail"),
    path("tutors/<int:pk>/photo/", views.TutorPhotoView.as_view(), name="tutor-photo"),
    path("tutor/profile/", views.OwnProfileView.as_view(), name="own-profile"),
    path("tutor/profile/photo/", views.OwnPhotoView.as_view(), name="own-photo"),
    path("staff/tutor-photos/<int:pk>/", views.StaffPhotoView.as_view(), name="staff-tutor-photo"),
]
