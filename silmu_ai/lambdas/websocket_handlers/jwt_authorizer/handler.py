import os
import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

USER_POOL_ID = os.environ["USER_POOL_ID"]  # e.g. us-east-1_XXXXXXX
CLIENT_ID = os.environ["CLIENT_ID"]  # Cognito App Client ID
REGION = os.environ.get("REGION", USER_POOL_ID.split("_")[0])

ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"
JWKS_URL = f"{ISSUER}/.well-known/jwks.json"

jwks_client = PyJWKClient(JWKS_URL)


def lambda_handler(event, context):
    token = event.get("authorizationToken") or event.get(
        "queryStringParameters", {}
    ).get("Authorization")
    if not token:
        raise Exception("Unauthorized")

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token).key

        decoded_token = jwt.decode(
            token, signing_key, algorithms=["RS256"], audience=CLIENT_ID, issuer=ISSUER
        )
    except InvalidTokenError as e:
        print("Token validation failed:", e)
        raise Exception("Unauthorized")

    # Build IAM policy
    return {
        "principalId": decoded_token["sub"],
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": event["methodArn"],
                }
            ],
        },
        "context": {
            "username": decoded_token.get("cognito:username", ""),
            "email": decoded_token.get("email", ""),
            "scope": decoded_token.get("scope", ""),
        },
    }
