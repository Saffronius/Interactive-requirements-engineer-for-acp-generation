# Policy Analysis Summary

**Generated:** 2025-08-17 22:06:30
**Extraction Confidence:** 85.0%

## Summary

Intent extracted: write, read_only access to s3, apigateway, kms, lambda services. Found 4 capabilities and 1 restrictions.

## Key Points

- Write access to lambda
- Write access to apigateway
- Read_Only access to s3
- Read_Only access to kms
- Deny: Prevent accidental modification of production databases

## Assumptions

- Provide target AWS account ID(s).
- Provide the exact principal ARN (who principal_ref).
- The ARNs of the Lambda functions, API Gateway configurations, and KMS keys are not specified and need to be provided.
- Validation: S3 read_only capability 's3_read' missing bucket-level ARN

## Risk Callouts

- Evidence confidence below 80% for s3_read.
- Extraction confidence 85% - manual review recommended
- HTTPS enforcement missing (aws:SecureTransport=true).
- No evidence citations attached for api_gateway_update — results may rely on heuristics.
- No evidence citations attached for kms_decrypt — results may rely on heuristics.
- No evidence citations attached for lambda_deploy — results may rely on heuristics.
- S3 read requires both bucket ARN (arn:aws:s3:::bucket) and object ARN (arn:aws:s3:::bucket/*).
- Validation: Capability 'kms_decrypt' has evidence with confidence < 80%
- Validation: Capability 'kms_decrypt' uses wildcard resources - explicit ARNs required
- Validation: Capability 's3_read' has evidence with confidence < 80%
- Validation: Condition key 'aws:CurrentTime' not allowed for service 'kms'
- Validation: Condition key 'aws:CurrentTime' not allowed for service 's3'
- Validation: Condition key 'aws:MultiFactorAuthPresent' not allowed for service 'kms'
- Validation: Condition key 'aws:MultiFactorAuthPresent' not allowed for service 's3'
- Validation: Unknown service in capability 'api_gateway_update': apigateway
- Validation: Unknown service in capability 'lambda_deploy': lambda
