from rest_framework.permissions import BasePermission
from ecommerce.extensions.edly_ecommerce_app.helpers import user_is_course_creator


class IsAdminOrCourseCreator(BasePermission):
    """
    Checks if logged in user is staff or a course creator.
    """

    def has_permission(self, request, view):
        is_admin = request.user.is_staff or request.user.is_superuser
        is_course_creator = user_is_course_creator(request)
        return is_admin or is_course_creator
