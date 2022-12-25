from django.urls import path, re_path
from codespace.views import (
    CreateCodeSpaceView,
    RetrieveCodeSpaceView,
    TokenCodeSpaceShareView,
)

app_name = "codespace"
urlpatterns = [
    path("codespace/", CreateCodeSpaceView.as_view(), name="create_codespace"),
    re_path(
        r"codespace/(?P<uuid>(tmp-)?[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})/",  # noqa
        RetrieveCodeSpaceView.as_view(),
        name="retrieve_codespace",
    ),
    path(
        "codespace/token/",
        TokenCodeSpaceShareView.as_view(),
        name="token_codespace_access",
    ),
]
