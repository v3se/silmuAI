def lambda_handler(event, context):
    print("Disconnect event:", event)
    return {"statusCode": 200, "body": "Disconnected."}
