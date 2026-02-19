from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl, RootModel


class InternalFederationNode(BaseModel):
    """Model for the definition of an internal or local node to be federated by the federation API."""

    name: Annotated[
        str, Field(validation_alias="NAME", serialization_alias="NodeName")
    ]
    api_url: Annotated[
        HttpUrl,
        Field(validation_alias="API_URL", serialization_alias="ApiURL"),
    ]


class InternalFederationNodes(RootModel[list[InternalFederationNode]]):
    pass
