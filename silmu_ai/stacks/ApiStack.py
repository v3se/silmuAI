from aws_cdk import aws_lambda as _lambda, aws_apigateway as apigw
from .BaseStack import BaseStack
from aws_solutions_constructs import aws_apigateway_lambda as apigw_lambda
from constructs import Construct


class ApiStack(BaseStack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        """Initialize the API stack.
        Args:
            scope (Construct): The scope in which this stack is defined.
            construct_id (str): The ID of the construct.
            **kwargs: Additional keyword arguments.
        """
        self.api = apigw_lambda.ApiGatewayToLambda(
            self,
            self.resource_name("PlantsEndpoint"),
            create_usage_plan=True,
            lambda_function_props=_lambda.FunctionProps(
                runtime=_lambda.Runtime.PYTHON_3_11,
                code=_lambda.Code.from_asset("silmu_ai/lambdas/plants_lambda"),
                handler="handler.handler",
            ),
            api_gateway_props=apigw.RestApiProps(
                default_method_options=apigw.MethodOptions(
                    authorization_type=apigw.AuthorizationType.NONE,
                    api_key_required=True,
                )
            ),
        )
