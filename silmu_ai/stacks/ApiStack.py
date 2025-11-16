from aws_cdk import aws_lambda as _lambda
from aws_cdk import CfnOutput
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk.aws_apigatewayv2 import (
    WebSocketApi,
    WebSocketStage,
    WebSocketRoute,
)
from aws_cdk.aws_apigatewayv2_authorizers import WebSocketLambdaAuthorizer
from aws_cdk.aws_apigatewayv2_integrations import WebSocketLambdaIntegration
from aws_cdk import BundlingOptions, DockerImage
from aws_cdk import aws_iam as iam
from aws_cdk import Duration
from .BaseStack import BaseStack
from constructs import Construct
import hashlib
import os


class ApiStack(BaseStack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        cognito_user_pool_id: str,
        cognito_client_id: str,
        conversation_table: dynamodb.Table,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        """Initialize the API stack.
        Args:
            scope (Construct): The scope in which this stack is defined.
            construct_id (str): The ID of the construct.
            **kwargs: Additional keyword arguments.
        """

        def _file_hash(path):
            with open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()

        requirements_hash = _file_hash(
            "silmu_ai/lambdas/websocket_handlers/jwt_authorizer/requirements.txt"
        )
        authorizer_handler = _lambda.Function(
            self,
            self.resource_name("AuthorizerHandler"),
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            environment={
                "USER_POOL_ID": cognito_user_pool_id,
                "CLIENT_ID": cognito_client_id,
            },
            code=_lambda.Code.from_asset(
                "silmu_ai/lambdas/websocket_handlers/jwt_authorizer",
                bundling=BundlingOptions(
                    image=DockerImage.from_registry("python:3.12"),
                    command=[
                        "bash",
                        "-c",
                        (
                            "pip install -r requirements.txt --target=. && "
                            "cp -r . /asset-output"
                        ),
                    ],
                    working_directory="/asset-input",
                ),
                asset_hash=requirements_hash,
            ),
        )

        connect_handler = _lambda.Function(
            self,
            self.resource_name("WebSocketConnectHandler"),
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset(
                "silmu_ai/lambdas/websocket_handlers/connect_handler"
            ),
        )

        disconnect_handler = _lambda.Function(
            self,
            self.resource_name("WebSocketDisconnectHandler"),
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset(
                "silmu_ai/lambdas/websocket_handlers/disconnect_handler"
            ),
        )

        plants_lambda_handler = _lambda.Function(
            self,
            self.resource_name("PlantsLambdaHandler"),
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset(
                "silmu_ai/lambdas/plants_lambda",
                bundling=BundlingOptions(
                    image=DockerImage.from_registry("python:3.12"),
                    command=[
                        "bash",
                        "-c",
                        (
                            "pip install -r requirements.txt --target=. && "
                            "cp -r . /asset-output"
                        ),
                    ],
                    working_directory="/asset-input",
                ),
            ),
            environment={
                "BEDROCK_REGION": "us-east-1",
                "DYNAMODB_REGION": "eu-central-1",
                "CONVERSATION_TABLE_NAME": conversation_table.table_name,
            },
            timeout=Duration.seconds(30),
        )

        plants_lambda_handler.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[
                    "arn:aws:bedrock:*:*:foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
                    "arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                ],
            )
        )
        conversation_table.grant_read_write_data(plants_lambda_handler)

        # Create the WebSocket API
        authorizer_name = self.resource_name("WebSocketApiAuthorizer")
        authorizer = WebSocketLambdaAuthorizer(
            authorizer_name,
            handler=authorizer_handler,
            identity_source=["route.request.querystring.Authorization"],
        )

        websocket_api_name = self.resource_name("WebSocketApi")
        self.websocket_api = WebSocketApi(
            self,
            websocket_api_name,
            api_name=websocket_api_name,
        )

        WebSocketRoute(
            self,
            self.resource_name("WebSocketConnectRoute"),
            web_socket_api=self.websocket_api,
            route_key="$connect",
            integration=WebSocketLambdaIntegration(
                self.resource_name("WebSocketConnectIntegration"),
                handler=connect_handler,
            ),
            authorizer=authorizer,
        )

        WebSocketRoute(
            self,
            self.resource_name("WebSocketDisconnectRoute"),
            web_socket_api=self.websocket_api,
            route_key="$disconnect",
            integration=WebSocketLambdaIntegration(
                self.resource_name("WebSocketDisconnectIntegration"),
                handler=disconnect_handler,
            ),
        )

        WebSocketRoute(
            self,
            self.resource_name("WebSocketDefaultRoute"),
            web_socket_api=self.websocket_api,
            route_key="$default",
            integration=WebSocketLambdaIntegration(
                self.resource_name("WebSocketDefaultIntegration"),
                handler=plants_lambda_handler,
            ),
        )

        WebSocketStage(
            self,
            self.resource_name("WebSocketStage"),
            web_socket_api=self.websocket_api,
            stage_name="dev",
            auto_deploy=True,
        )

        plants_lambda_handler.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["execute-api:ManageConnections"],
                resources=[
                    f"arn:aws:execute-api:{self.region}:{self.account}:{self.websocket_api.api_id}/dev/POST/@connections/*"
                ],
            )
        )

        CfnOutput(
            self,
            self.resource_name("WebSocketApiEndpoint"),
            value=f"wss://{self.websocket_api.api_id}.execute-api.{self.region}.amazonaws.com/dev",
            description="WebSocket API endpoint",
        )
