from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from app.models.phone_pressure import PhonePressureAction
from app.settings import get_settings

def get_graphql_client():
    settings = get_settings()

    transport = AIOHTTPTransport(url=settings.graphql_api_url)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    return client

def create_widget_action(action: PhonePressureAction):
    client = get_graphql_client()

    mutation = gql("""
        mutation($activist: ActivistInput!, $widget_id: Int!, $input: WidgetActionInput!) {
            create_widget_action(activist: $activist, widget_id: $widget_id, input: $input) {
                data
            }
        }
    """)

    variables = {
        "activist": action.activist,
        "input": action.input,
        "widget_id": action.widget_id,
    }

    return client.execute(mutation, variable_values=variables)
