from pathlib import Path
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field, RootModel

# from enum import Enum


def path_has_leading_slash(path: str) -> str:
    # TODO: Should we prepend the leading slash automatically?
    if path and not path.startswith("/"):
        raise ValueError("Base path must start with a leading slash.")
    return path


def domain_has_no_protocol(domain: str) -> str:
    if domain.startswith(("http://", "https://")):
        raise ValueError(
            "Domain name must not include a protocol (http:// or https://)."
        )
    return domain


class Graph(BaseModel):
    graph_username: Annotated[
        str, Field(alias="NB_GRAPH_USERNAME", default="DBUSER")
    ]
    graph_db: Annotated[
        str, Field(alias="NB_GRAPH_DB", default="repositories/my_db")
    ]
    graph_data: Annotated[Path, Field(alias="NB_GRAPH_DATA", default="./data")]
    graph_port_host: Annotated[
        str, Field(alias="NB_GRAPH_PORT_HOST", default="7200")
    ]
    graph_secrets_path: Annotated[
        Path, Field(alias="NB_GRAPH_SECRETS_PATH", default="./secrets")
    ]
    graph_memory: Annotated[str, Field(alias="NB_GRAPH_MEMORY", default="2G")]


class NodeAPI(BaseModel):
    return_agg: Annotated[bool, Field(alias="NB_RETURN_AGG", default=True)]
    napi_base_path: Annotated[
        str,
        Field(alias="NB_NAPI_BASE_PATH", default=""),
        AfterValidator(path_has_leading_slash),
    ]
    napi_domain: Annotated[
        str,
        Field(alias="NB_NAPI_DOMAIN", default=""),
        AfterValidator(domain_has_no_protocol),
    ]
    napi_port_host: Annotated[
        str, Field(alias="NB_NAPI_PORT_HOST", default="8000")
    ]
    napi_min_cell_size: Annotated[
        int, Field(alias="NB_MIN_CELL_SIZE", default=0)
    ]
    napi_tag: Annotated[str, Field(alias="NB_NAPI_TAG", default="latest")]
    config: Annotated[str, Field(alias="NB_CONFIG", default="Neurobagel")]


class FedAPI(BaseModel):
    fapi_base_path: Annotated[
        str,
        Field(alias="NB_FAPI_BASE_PATH", default=""),
        AfterValidator(path_has_leading_slash),
    ]
    fapi_domain: Annotated[
        str,
        Field(alias="NB_FAPI_DOMAIN", default=""),
        AfterValidator(domain_has_no_protocol),
    ]
    fapi_port_host: Annotated[
        str, Field(alias="NB_FAPI_PORT_HOST", default="8080")
    ]
    federate_remote_public_nodes: Annotated[
        bool, Field(alias="NB_FEDERATE_REMOTE_PUBLIC_NODES", default=True)
    ]
    fapi_tag: Annotated[str, Field(alias="NB_FAPI_TAG", default="latest")]


class Query(BaseModel):
    # TODO: Consider constructing this URL automatically for production portal deployments?
    api_query_url: Annotated[
        str, Field(alias="NB_API_QUERY_URL", default="http://localhost:8080")
    ]
    query_app_base_path: Annotated[
        str,
        Field(alias="NB_QUERY_APP_BASE_PATH", default="/"),
        AfterValidator(path_has_leading_slash),
    ]
    query_domain: Annotated[
        str,
        Field(alias="NB_QUERY_DOMAIN", default=""),
        AfterValidator(domain_has_no_protocol),
    ]
    query_port_host: Annotated[
        str, Field(alias="NB_QUERY_PORT_HOST", default="3000")
    ]
    # TODO: Ensure that this variable is not exported to the output .env if set to None
    query_header_script: Annotated[
        str | None,
        Field(
            alias="NB_QUERY_HEADER_SCRIPT",
            default=None,
        ),
    ]


class Experimental(BaseModel):
    enable_auth: Annotated[bool, Field(alias="NB_ENABLE_AUTH", default=False)]
    # TODO: Ensure that this variable is not exported to the output .env if set to None
    query_client_id: Annotated[
        str | None, Field(alias="NB_QUERY_CLIENT_ID", default=None)
    ]


# class ProfileEnum(str, Enum):
#     NODE = "node"
#     PORTAL = "portal"

#     @classmethod
#     def get_values(cls) -> list[str]:
#         return [member.value for member in cls]

# class ComposeProfile(BaseModel):
#     profile: Annotated[
#         ProfileEnum,
#         Field(alias="COMPOSE_PROFILES"),
#     ]


class NodeCompose(BaseModel):
    profile: Annotated[
        Literal["node"],
        Field(alias="COMPOSE_PROFILES", default="node"),
    ]
    project_name: Annotated[
        str, Field(alias="COMPOSE_PROJECT_NAME", default="neurobagel_node")
    ]


class PortalCompose(BaseModel):
    profile: Annotated[
        Literal["portal"],
        Field(alias="COMPOSE_PROFILES", default="portal"),
    ]
    project_name: Annotated[
        str, Field(alias="COMPOSE_PROJECT_NAME", default="neurobagel_portal")
    ]


class TestingCompose(BaseModel):
    project_name: Annotated[
        str,
        Field(alias="COMPOSE_PROJECT_NAME", default="neurobagel_testing"),
    ]


class Node(BaseModel):
    service_node_api: Annotated[
        NodeAPI,
        Field(alias="service:node-api", default_factory=NodeAPI),
    ]
    service_graph: Annotated[
        Graph, Field(alias="service:graph", default_factory=Graph)
    ]
    compose: Annotated[
        NodeCompose, Field(alias="compose", default_factory=NodeCompose)
    ]


class Portal(BaseModel):
    service_federation_api: Annotated[
        FedAPI,
        Field(alias="service:federation-api", default_factory=FedAPI),
    ]
    service_query: Annotated[
        Query, Field(alias="service:query", default_factory=Query)
    ]
    compose: Annotated[
        PortalCompose,
        Field(alias="compose", default_factory=PortalCompose),
    ]


class Testing(BaseModel):
    service_node_api: Annotated[
        NodeAPI,
        Field(alias="service:node-api", default_factory=NodeAPI),
    ]
    service_graph: Annotated[
        Graph, Field(alias="service:graph", default_factory=Graph)
    ]
    service_federation_api: Annotated[
        FedAPI,
        Field(alias="service:federation-api", default_factory=FedAPI),
    ]
    service_query: Annotated[
        Query, Field(alias="service:query", default_factory=Query)
    ]
    compose: Annotated[
        TestingCompose,
        Field(alias="compose", default_factory=TestingCompose),
    ]


class ConfigFile(RootModel[Node | Portal | Testing]):
    pass


COMPOSE_PROFILE_TO_CLASS_MAP = {
    "node": Node,
    "portal": Portal,
}
