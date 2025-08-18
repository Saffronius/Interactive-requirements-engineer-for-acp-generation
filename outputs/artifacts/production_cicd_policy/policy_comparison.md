# Policy Comparison Report

**Generated:** 2025-08-17 22:06:30
**Baseline Confidence:** Deterministic (100%)
**Candidate Confidence:** 100.0%

## Executive Summary

- **Baseline Statements:** 0
- **Candidate Statements:** 2
- **Statement Difference:** 2
- **Actions Overlap:** 0.0%
- **Resources Overlap:** 0.0%

## Detailed Analysis

### Actions Comparison
- **Baseline Only:** 
- **Candidate Only:** dynamodb:PutItem, logs:PutLogEvents, lambda:UpdateAlias, s3:ListBucket, lambda:CreateFunction, apigateway:GET, apigateway:PATCH, rds:ModifyDBCluster, rds:DeleteDBInstance, dynamodb:BatchWriteItem
- **Common Actions:** 0

### Resources Comparison
- **Baseline Only:** 0 resources
- **Candidate Only:** 10 resources
- **Common Resources:** 0

## Side-by-Side Policies

### Baseline Policy
```json
{
  "Version": "2012-10-17",
  "Statement": []
}
```

### Candidate Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCICDPipelineOperations",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:GetFunction",
        "lambda:ListFunctions",
        "lambda:TagResource",
        "lambda:PublishVersion",
        "lambda:CreateAlias",
        "lambda:UpdateAlias",
        "apigateway:GET",
        "apigateway:PUT",
        "apigateway:POST",
        "apigateway:PATCH",
        "apigateway:DELETE",
        "apigateway:Deploy",
        "apigateway:UpdateRestApiPolicy",
        "apigateway:ManageConnections",
        "s3:GetObject",
        "s3:ListBucket",
        "kms:Decrypt",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": [
        "arn:aws:lambda:us-east-1:123456789012:function:*",
        "arn:aws:lambda:us-east-1:123456789012:function:*:alias/*",
        "arn:aws:apigateway:us-east-1::/restapis/*",
        "arn:aws:apigateway:us-east-1::/apis/*",
        "arn:aws:s3:::prod-deployments",
        "arn:aws:s3:::prod-deployments/*",
        "arn:aws:kms:us-east-1:123456789012:key/abcdef12-3456-7890-abcd-ef1234567890",
        "arn:aws:logs:us-east-1:123456789012:log-group:*",
        "arn:aws:logs:us-east-1:123456789012:log-group:*:log-stream:*"
      ],
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": "10.0.0.0/8"
        },
        "Bool": {
          "aws:MultiFactorAuthPresent": "true"
        },
        "DateGreaterThanEquals": {
          "aws:CurrentTime": "2025-01-01T14:00:00Z"
        },
        "DateLessThanEquals": {
          "aws:CurrentTime": "2025-01-01T23:00:00Z"
        },
        "ForAnyValue:StringEquals": {
          "kms:EncryptionContext:SecretPurpose": "CiCdDeployment"
        }
      }
    },
    {
      "Sid": "DenyProductionDatabaseWrites",
      "Effect": "Deny",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:BatchWriteItem",
        "rds:ModifyDBInstance",
        "rds:ModifyDBCluster",
        "rds:DeleteDBInstance",
        "rds:DeleteDBCluster"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/Environment": "Production"
        }
      }
    }
  ]
}
```

## Recommendations

- ⚠️  Low action overlap - verify intent alignment
- ⚠️  Baseline policy is empty - review SpecDSL
