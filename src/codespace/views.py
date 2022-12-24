from rest_framework import generics, permissions
from codespace.serializers import CodeSpaceSerializer, TmpCodeSpaceSerializer
from codespace.permissions import IsCodeSpaceOwner
from rest_framework.response import Response
from core.models import CodeSpace, TmpCodeSpace
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import status
from typing import Type, Union, List


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


class RetrieveCodeSpaceView(generics.RetrieveAPIView):
    """View used to retrieve codespace data."""

    # Regular codespace
    codespace_class = CodeSpace
    codespace_serializer_class = CodeSpaceSerializer
    codespace_permission_classes = (permissions.IsAuthenticated, IsCodeSpaceOwner)

    # Tmp codespace
    tmp_codespace_class = TmpCodeSpace
    tmp_codespace_serializer_class = TmpCodeSpaceSerializer
    tmp_codespace_permission_classes = (permissions.AllowAny,)

    def get_permissions(self) -> List[Type[permissions.BasePermission]]:
        """
        Instantiates and returns the list of permissions
        depending of codespace type
        """

        print(self.request.user.is_authenticated)

        if self.kwargs.get("uuid", "").startswith("tmp-"):
            return [
                permission() for permission in self.tmp_codespace_permission_classes
            ]
        else:
            print(self.request.user.is_authenticated)
            return [permission() for permission in self.codespace_permission_classes]

    def get_serializer_class(
        self,
    ) -> Union[Type[CodeSpaceSerializer], Type[TmpCodeSpaceSerializer]]:
        """
        Return either codespace or tmp codespace
        serializer class
        """

        obj_uuid = self.kwargs.get("uuid", "")
        if obj_uuid.startswith("tmp-"):
            return self.tmp_codespace_serializer_class
        else:
            return self.codespace_serializer_class

    def get_object(self) -> Union[Type[CodeSpace], Type[TmpCodeSpace], None]:
        obj_uuid = self.kwargs.get("uuid", "")
        if obj_uuid.startswith("tmp-"):
            try:
                obj = TmpCodeSpace.objects.get(uuid=obj_uuid)
            except TmpCodeSpace.DoesNotExist as e:
                raise Http404(e)
        else:
            obj = get_object_or_404(CodeSpace, uuid=obj_uuid)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

    def retrieve(self, request, *args, **kwargs) -> Type[Response]:
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get(self, request, *args, **kwargs) -> Type[Response]:
        return self.retrieve(request, *args, **kwargs)
