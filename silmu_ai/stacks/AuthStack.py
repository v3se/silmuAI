from aws_cdk import (
    aws_cognito as cognito,
)
from .BaseStack import BaseStack
from constructs import Construct


class AuthStack(BaseStack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        """Initialize the Cognito authentication stack."""

        self.user_pool = cognito.UserPool(
            self,
            self.resource_name("UserPool"),
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True, username=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=self.default_removal_policy,
        )

        # Create User Pool Client (for frontend authentication)
        self.user_pool_client = cognito.UserPoolClient(
            self,
            self.resource_name("UserPoolClient"),
            user_pool=self.user_pool,
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=True,
                ),
                scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.EMAIL],
                callback_urls=["http://localhost:3000/"],  # Update for production
                logout_urls=["http://localhost:3000/"],
            ),
        )

        # Output values for use in frontend/backend configuration
        self.user_pool_id = self.user_pool.user_pool_id
        self.user_pool_client_id = self.user_pool_client.user_pool_client_id
