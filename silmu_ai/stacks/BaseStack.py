import re
import aws_cdk
from aws_cdk import Stack
from constructs import Construct


class BaseStack(Stack):
    """Base class for all stacks in the Silmu AI project."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """Initialize the base stack.
        Args:
            scope (Construct): The scope in which this stack is defined.
            construct_id (str): The ID of the construct.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(scope, construct_id, **kwargs)

        self.suffix = self._get_suffix()

        self.default_removal_policy = aws_cdk.RemovalPolicy.DESTROY

    def _get_suffix(self):
        """Get a safe suffix for the branch name based on the environment context."""
        environment = self.node.try_get_context("environment") or "dev"
        # Replace non-alphanumeric characters with nothing
        safe_env = re.sub(r"[^a-zA-Z0-9]", "", environment.lower())
        return safe_env[:17]

    def resource_name(self, base: str):
        return f"{base}-{self.suffix}"
