def lambda_handler(event, context):
    """
    Dummy Lambda handler for WebSocket $connect route.
    """
    print("Connect event:", event)
    return {"statusCode": 200, "body": "Connected."}
