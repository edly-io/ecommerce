from rest_framework.permissions import BasePermission
from ecommerce.extensions.edly_ecommerce_app.helpers import user_is_course_creator
from ecommerce.extensions.edly_ecommerce_app.api.v1.constants import EDLY_PANEL_WORKER_USER


class IsAdminOrCourseCreator(BasePermission):
    """
    Checks if logged in user is staff or a course creator.
    """

    def has_permission(self, request, view):
        is_admin = request.user.is_staff or request.user.is_superuser
        is_course_creator = user_is_course_creator(request)
        return is_admin or is_course_creator


class CanAccessSiteCreation(BasePermission):
    """
    Checks if a user has the access to create and update methods for sites.
    """

    def has_permission(self, request, view):
        """
        Checks for user's permission for current site.
        """
        return request.user.is_staff and request.user.username == EDLY_PANEL_WORKER_USER
