from typing import Annotated

from fastapi import Depends, Request

from utils.request_meta import RequestMeta, get_request_meta


def get_meta_dep(request: Request) -> RequestMeta:
    return get_request_meta(request)

request_meta_dep = Annotated[RequestMeta, Depends(get_meta_dep)]