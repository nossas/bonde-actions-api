from typing import Annotated

from fastapi import Depends
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from app.config import settings


transport = AIOHTTPTransport(
    settings.graphql_api_url,
    ssl=not settings.debug,
    headers=(
        {"x-hasura-admin-secret": settings.graphql_api_token}
        if settings.graphql_api_token
        else None
    ),
)


async def get_graphql_client():
    async with Client(transport=transport) as graphql_client:
        yield graphql_client


GraphQLClientDep = Annotated[Client, Depends(get_graphql_client)]

# Queries e Mutations BONDE API

create_widget_action_gql = gql(
    """
    mutation($activist: ActivistInput!, $widget_id: Int!, $input: WidgetActionInput!) {
        create_widget_action(activist: $activist, widget_id: $widget_id, input: $input) {
            data
        }
    }
"""
)


get_widget_gql = gql(
    """
    query($widget_id: Int!) {
        widgets_by_pk(id: $widget_id) {
            id
            kind
            settings
        }
    }
"""
)
