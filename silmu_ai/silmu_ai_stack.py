from aws_cdk import (
    Stack,
    aws_s3 as s3,  # Add this import
)
from constructs import Construct


class SilmuAiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
