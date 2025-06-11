import boto3
import json


def lambda_handler(event, context):
    print("Default route event:", event)
    connection_id = event["requestContext"]["connectionId"]
    domain = event["requestContext"]["domainName"]
    stage = event["requestContext"]["stage"]

    apigw_management = boto3.client(
        "apigatewaymanagementapi", endpoint_url=f"https://{domain}/{stage}"
    )

    message = {"message": "Default route invoked."}
    apigw_management.post_to_connection(
        ConnectionId=connection_id, Data=json.dumps(message).encode("utf-8")
    )

    return {"statusCode": 200}
