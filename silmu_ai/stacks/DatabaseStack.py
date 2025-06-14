from aws_cdk import (
    aws_dynamodb as dynamodb,
)
from .BaseStack import BaseStack
from constructs import Construct


class DatabaseStack(BaseStack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        """Initialize the Database stack.
        Args:
            scope (Construct): The scope in which this stack is defined.
            construct_id (str): The ID of the construct.
            **kwargs: Additional keyword arguments.
        """
        # Create DynamoDB table for conversation history
        self.conversation_table = dynamodb.Table(
            self,
            self.resource_name("RecipeConversationHistory"),
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=self.default_removal_policy,
        )
