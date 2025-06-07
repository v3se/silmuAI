import aws_cdk as core
import aws_cdk.assertions as assertions

from silmu_ai.silmu_ai_stack import SilmuAiStack

# example tests. To run these tests, uncomment this file along with the example
# resource in silmu_ai/silmu_ai_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SilmuAiStack(app, "silmu-ai")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
