from rest_framework import generics, permissions, exceptions
from codespace.serializers import CodeSpaceSerializer, TmpCodeSpaceSerializer
from codespace.permissions import IsCodeSpaceOwner, IsCodeSpaceAccessTokenValid
from codespace.pagination import PageNumberPagination
from rest_framework.response import Response
from core.models import CodeSpace, TmpCodeSpace
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework import status
from typing import Type, Union
from django.db.models.query import QuerySet


class CreateCodeSpaceView(generics.CreateAPIView):
    """View responsible for creating new codespace."""

    codespace_serializer_class = CodeSpaceSerializer
    tmp_codespace_serializer_class = TmpCodeSpaceSerializer

    def get_serializer_class(
        self,
    ) -> Union[Type[CodeSpaceSerializer], Type[TmpCodeSpaceSerializer]]:
        # if user is not authenticated create temporary codespace
        if self.request.user.is_authenticated:
            return self.codespace_serializer_class
        else:
            return self.tmp_codespace_serializer_class

    def create(self, request, *args, **kwargs) -> Type[Response]:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(
        self, serializer: Union[Type[CodeSpaceSerializer], Type[TmpCodeSpaceSerializer]]
    ) -> None:
        serializer.save(created_by=self.request.user)


class CodeSpaceListView(generics.ListAPIView):
    """View used to get list of codespaces created by authenticated user"""

    serializer_class = CodeSpaceSerializer
    queryset = CodeSpace.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPagination

    def get_queryset(self) -> Type[QuerySet]:
        """Return a queryset of CodeSpace created by authenticated user"""
        return self.queryset.filter(
            created_by=self.request.user,
        ).order_by("-created_at")


class RetrieveUpdateDestroyCodeSpaceView(generics.RetrieveUpdateDestroyAPIView):
    """View used to retrieve, update or delete regular codespace data."""

    serializer_class = CodeSpaceSerializer
    permission_classes = (permissions.IsAuthenticated, IsCodeSpaceOwner)

    def get_object(self) -> Union[Type[CodeSpace], None]:
        obj_uuid = self.kwargs.get("uuid", "")
        obj = get_object_or_404(CodeSpace, uuid=obj_uuid)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj


class RetrieveDestroyTmpCodeSpaceView(generics.RetrieveDestroyAPIView):
    """View used to retrieve or delete temporary codespace data."""

    serializer_class = TmpCodeSpaceSerializer
    permission_classes = (permissions.AllowAny,)

    def get_object(self) -> Union[Type[CodeSpace], None]:
        obj_uuid = self.kwargs.get("tmp_uuid", "")

        try:
            obj = TmpCodeSpace.objects.get(uuid=obj_uuid)
        except TmpCodeSpace.DoesNotExist as e:
            raise Http404(e)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj


class RetrieveCodeSpaceAccessTokenView(generics.RetrieveAPIView):
    """View used to retrieve code space data using
    access token generated by CodeSpaceAccessToken class"""

    # used by IsCodeSpaceAccessTokenValid to update kwargs with codespace uuid
    codespace_uuid_kwarg_key = "uuid"
    serializer_class = CodeSpaceSerializer
    permission_classes = (IsCodeSpaceAccessTokenValid,)

    def get_object(self) -> Union[Type[CodeSpace], None]:
        # uuid is in kwargs thanks to IsCodeSpaceAccessTokenValid
        uuid = self.kwargs.get("uuid")
        return get_object_or_404(CodeSpace, uuid=uuid)

    def permission_denied(self, request, message=None, code=None):
        """
        Override this method to not raise NotAuthenticated since
        this view doesn't require authentication
        """

        raise exceptions.PermissionDenied(detail=message, code=code)


class CodeSpaceSaveChangesView(generics.GenericAPIView):
    """
    View used to save code changes stored in redis
    to postgres database
    """

    # used by IsCodeSpaceAccessTokenValid to update kwargs with codespace uuid
    codespace_uuid_kwarg_key = "uuid"
    # permission classes used if endpoint accessed with token
    token_permission_classes = (IsCodeSpaceAccessTokenValid,)
    # permission classes used if endpoint accessed with codespace uuid
    uuid_permission_classes = (IsCodeSpaceOwner,)

    def save_changes(self, request, *args, **kwargs):
        """
        Method used to saved redis changes to postgres
        """

        obj = self.get_object()
        self.check_object_permissions(self.request, obj)

        try:
            CodeSpace.save_redis_changes(codespace=obj)
        except ObjectDoesNotExist as e:
            raise exceptions.NotFound(detail=str(e))

        return Response(
            data={"detail": "CodeSpace data saved successfully"},
            status=status.HTTP_200_OK,
        )

    def get_object(self) -> Type[CodeSpace]:
        """
        Return CodeSpace object
        """
        obj = CodeSpace.objects.filter(uuid=self.kwargs.get("uuid"))
        if obj.exists():
            # use filter to don't fire post_get signal
            return obj.first()
        else:
            raise exceptions.NotFound(detail="CodeSpace does not exists")

    def get_permissions(self):
        """
        Based on url parameter returns corresponding permission classes
        """

        if "token" in self.kwargs:
            return [permission() for permission in self.token_permission_classes]
        elif "uuid" in self.kwargs:
            return [permission() for permission in self.uuid_permission_classes]

    def patch(self, request, *args, **kwargs):
        return self.save_changes(request, *args, **kwargs)
