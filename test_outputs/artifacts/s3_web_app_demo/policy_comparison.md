# Policy Comparison Report

**Generated:** 2025-08-16 23:15:04
**Baseline Confidence:** Deterministic (100%)
**Candidate Confidence:** 100.0%

## Executive Summary

- **Baseline Statements:** 0
- **Candidate Statements:** 3
- **Statement Difference:** 3
- **Actions Overlap:** 0.0%
- **Resources Overlap:** 0.0%

## Detailed Analysis

### Actions Comparison
- **Baseline Only:** 
- **Candidate Only:** s3:GetObject, s3:ListBucket, kms:Decrypt
- **Common Actions:** 0

### Resources Comparison
- **Baseline Only:** 0 resources
- **Candidate Only:** 3 resources
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
      "Sid": "AllowListSpecificBucket",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::example-bucket"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "true"
        }
      }
    },
    {
      "Sid": "AllowGetObjectFromBucket",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::example-bucket/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "true"
        }
      }
    },
    {
      "Sid": "AllowKMSDecryptIfEncrypted",
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": [
        "arn:aws:kms:us-east-1:123456789012:key/EXAMPLE-KEY-ID"
      ]
    }
  ]
}
```

## Recommendations

- ⚠️  Significant structural differences - review carefully
- ⚠️  Low action overlap - verify intent alignment
- ⚠️  Baseline policy is empty - review SpecDSL
