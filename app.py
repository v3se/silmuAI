#!/usr/bin/env python3
import os

import aws_cdk as cdk

from silmu_ai.stacks.ApiStack import ApiStack
from silmu_ai.stacks.DatabaseStack import DatabaseStack


app = cdk.App()
ApiStack(
    app,
    "SilmuAiApiStack",
)

DatabaseStack(app, "SilmuAiDatabaseStack")

app.synth()
