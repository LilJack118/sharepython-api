from rest_framework import permissions
from datetime import datetime
from codespace.tokens import codespace_access_token_generator


class IsObjectOwner(permissions.BasePermission):
    """
    Generic Permission that allows to check if request.user
    is object owner or not. Object owner field is determined
    by class attribute 'object_owner_field'
    """

    object_owner_field = "owner"

    def has_object_permission(self, request, view, obj):
        return getattr(obj, self.object_owner_field) == request.user


class IsCodeSpaceOwner(IsObjectOwner):
    """
    Permission used to check if request.user is
    codespace owner
    """

    object_owner_field = "created_by"


class IsCodeSpaceAccessTokenValid(permissions.BasePermission):
    """
    Permission used to check if codespace access token is valid and not expired.
    Token can be send as url parameter or post data. If token is valid view kwargs
    will be updated with codespace_uuid and mode
    """

    message = "Codespace access token is not valid or expired"

    def has_permission(self, request, view) -> bool:
        token = view.kwargs.get("token", "") or request.data.get("token", "")

        try:
            (
                codespace_uuid,
                expire_ts,
                mode,
            ) = codespace_access_token_generator.decrypt_token(token)
        except Exception:
            return False

        if datetime.now() > datetime.fromtimestamp(int(expire_ts)):
            return False

        view.kwargs.update(
            {
                # add codespace uuid to kwargs
                getattr(
                    view, "codespace_uuid_kwarg_key", "codespace_uuid"
                ): codespace_uuid,
                # add token mode to kwargs
                getattr(view, "mode_kwarg_key", "mode"): mode,
            }
        )
        return True
