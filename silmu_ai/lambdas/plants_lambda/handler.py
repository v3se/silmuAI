import os
import time
import boto3
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from boto3.dynamodb.conditions import Key
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware

sts = boto3.client("sts")
account_id = sts.get_caller_identity()["Account"]

BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
DYNAMODB_REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-central-1")

MODEL_ID = "arn:aws:bedrock:us-east-1:{}:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0".format(
    account_id
)
DDB_TABLE = os.environ.get(
    "CONVERSATION_TABLE_NAME",
    "SilmuAiDatabaseStack-ConversationHistorytestE9173A78-1QUM5VKFBKL69",
)

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "initial_prompt.txt")
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
dynamodb = boto3.resource("dynamodb", region_name=DYNAMODB_REGION)
table = dynamodb.Table(DDB_TABLE)  # type: ignore

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_history(user_id):
    response = table.query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=True,
    )
    history = response.get("Items", [])
    messages = [{"role": "assistant", "content": [{"text": SYSTEM_PROMPT}]}]
    for item in history:
        messages.append({"role": item["role"], "content": [{"text": item["text"]}]})
    return messages


def save_message(user_id, role, text):
    table.put_item(
        Item={
            "user_id": user_id,
            "timestamp": int(time.time() * 1000),
            "role": role,
            "text": text,
        }
    )


def query_bedrock_with_history(user_id, user_prompt: str) -> str:
    history = get_history(user_id)
    # Remove any messages with blank text
    history = [
        msg
        for msg in history
        if msg.get("content") and msg["content"][0].get("text", "").strip()
    ]
    history.append({"role": "user", "content": [{"text": user_prompt}]})
    try:
        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=history,
            inferenceConfig={
                "maxTokens": 4096,
                "temperature": 0.5,
                "topP": 0.9,
            },
        )
        result = response["output"]["message"]
        answer = (
            result["content"][0]["text"]
            if "content" in result and result["content"]
            else "No response from model."
        )
    except Exception as e:
        answer = f"Error querying Bedrock: {str(e)}"
    save_message(user_id, "user", user_prompt)
    save_message(user_id, "assistant", answer)
    return answer


@app.post("/plants/care-instructions")
async def care_instructions(request: Request):
    data = await request.json()
    user_id = data.get("user_id", "anonymous")
    user_prompt = data.get("prompt", "How do I care for my plant?")
    answer = query_bedrock_with_history(user_id, user_prompt)
    return JSONResponse(content={"answer": answer})


# --- WebSocket handler for API Gateway $default route ---
def lambda_handler(event, context):
    # Detect WebSocket event
    if "requestContext" in event and "connectionId" in event["requestContext"]:
        connection_id = event["requestContext"]["connectionId"]
        domain = event["requestContext"]["domainName"]
        stage = event["requestContext"]["stage"]

        # Parse user_id and prompt from the message body (assume JSON)
        try:
            body = event.get("body", "")
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        user_id = data.get("user_id", "anonymous")
        user_prompt = data.get("prompt", "How do I care for my plant?")

        apigw_management = boto3.client(
            "apigatewaymanagementapi", endpoint_url=f"https://{domain}/{stage}"
        )

        # Prepare conversation history
        history = get_history(user_id)
        # Remove any messages with blank text
        history = [
            msg
            for msg in history
            if msg.get("content") and msg["content"][0].get("text", "").strip()
        ]
        # Add the new user prompt
        history.append({"role": "user", "content": [{"text": user_prompt}]})

        partial_answer = ""
        try:
            # Stream response from Bedrock
            streaming_response = bedrock.converse_stream(
                modelId=MODEL_ID,
                messages=history,
                inferenceConfig={
                    "maxTokens": 4096,
                    "temperature": 0.5,
                    "topP": 0.9,
                },
            )

            for chunk in streaming_response["stream"]:
                if "contentBlockDelta" in chunk:
                    text = chunk["contentBlockDelta"]["delta"]["text"]
                    partial_answer += text  # <-- accumulate the answer!
                    apigw_management.post_to_connection(
                        ConnectionId=connection_id,
                        Data=json.dumps({"token": text}).encode("utf-8"),
                    )

            # Save the full answer at the end
            save_message(user_id, "user", user_prompt)
            save_message(user_id, "assistant", partial_answer)

            apigw_management.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps({"done": True}).encode("utf-8"),
            )
        except Exception as e:
            apigw_management.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(
                    {"error": f"Error streaming from Bedrock: {str(e)}"}
                ).encode("utf-8"),
            )
        return {"statusCode": 200}

    # Fallback: HTTP (FastAPI) via Mangum
    return handler(event, context)


handler = Mangum(app)
