from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_iam as iam,
    CfnOutput,
    RemovalPolicy,
)
from constructs import Construct


class FrontendStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # S3 bucket for static site
        site_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            website_index_document="index.html",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Create OAC (Origin Access Control)
        oac = cloudfront.CfnOriginAccessControl(
            self,
            "OAC",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name="FrontendOAC",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4",
                description="OAC for S3 bucket",
            ),
        )

        # CloudFront distribution
        distribution = cloudfront.CfnDistribution(
            self,
            "FrontendDistribution",
            distribution_config=cloudfront.CfnDistribution.DistributionConfigProperty(
                enabled=True,
                default_root_object="index.html",
                origins=[
                    cloudfront.CfnDistribution.OriginProperty(
                        domain_name=site_bucket.bucket_regional_domain_name,
                        id="S3Origin",
                        s3_origin_config=cloudfront.CfnDistribution.S3OriginConfigProperty(
                            origin_access_identity=""
                        ),
                        origin_access_control_id=oac.ref,
                    )
                ],
                default_cache_behavior=cloudfront.CfnDistribution.DefaultCacheBehaviorProperty(
                    target_origin_id="S3Origin",
                    viewer_protocol_policy="redirect-to-https",
                    allowed_methods=["GET", "HEAD"],
                    cached_methods=["GET", "HEAD"],
                    forwarded_values=cloudfront.CfnDistribution.ForwardedValuesProperty(
                        query_string=False,
                        cookies=cloudfront.CfnDistribution.CookiesProperty(
                            forward="none"
                        ),
                    ),
                ),
            ),
        )

        # Grant CloudFront (OAC) access to the bucket
        site_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[site_bucket.arn_for_objects("*")],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{distribution.ref}"
                    }
                },
            )
        )

        # Deploy static files to S3
        s3deploy.BucketDeployment(
            self,
            "DeployReactApp",
            sources=[s3deploy.Source.asset("src/frontend/silmuai-chatbot/build")],
            destination_bucket=site_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )

        CfnOutput(
            self, "CloudFrontURL", value=f"https://{distribution.attr_domain_name}"
        )
