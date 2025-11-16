#!/usr/bin/env python3
import os

import aws_cdk as cdk

from silmu_ai.stacks.ApiStack import ApiStack
from silmu_ai.stacks.DatabaseStack import DatabaseStack
from silmu_ai.stacks.AuthStack import AuthStack
from silmu_ai.stacks.FrontendStack import FrontendStack


app = cdk.App()
silmu_auth_stack = AuthStack(app, "SilmuAiAuthStack")

silmu_database_stack = DatabaseStack(app, "SilmuAiDatabaseStack")

ApiStack(
    app,
    "SilmuAiApiStack",
    cognito_user_pool_id=silmu_auth_stack.user_pool.user_pool_id,
    cognito_client_id=silmu_auth_stack.user_pool_client.user_pool_client_id,
    conversation_table=silmu_database_stack.conversation_table,
)

FrontendStack(app, "FrontendStack")

app.synth()
