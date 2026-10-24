# Serverless URL Shortener on AWS

A serverless web app for creating short URLs. CloudFront securely (HTTPS) and quickly (CDN) serves the static frontend from a private S3 Bucket. API calls are made through API Gateway and served by Lambda function(s), providing a robust and secure backend, while DynamoDB stores records of links.

🔗 **Live demo:** [go.yarmohammadi.com](https://go.yarmohammadi.com)

```mermaid
flowchart TD
    Browser[Browser] --> Domain[go.yourdomain.com]
    Domain --> CF[CloudFront Distribution]

    CF -->|Static Frontend| S3[(S3 Private Bucket)]
    CF -->|/api/*| APIGW[API Gateway HTTP API]

    APIGW --> Lambda[Lambda Function]
    Lambda --> DynamoDB[(DynamoDB Table)]
    Lambda --> Logs[CloudWatch Logs / Alarms]
```

## Architecture

- **CloudFront** delivers the frontend and routes API requests.
- **S3** stores the static frontend privately.
- **API Gateway** exposes application endpoints.
- **Lambda** creates, retrieves, and redirects short URLs and tracks click counts.
- **DynamoDB** stores short codes, destination URLs, expiration, and click counts.
- **CloudWatch** stores logs and monitors Lambda errors.
- **AWS Budgets** sends an alert at 80% of a $5 monthly budget.

## Features

- Create a short URL from a valid `http://` or `https://` link
- Redirect short codes with HTTP `302`
- List recently created links
- Count clicks
- Expire links automatically using DynamoDB TTL
- HTTPS through CloudFront
- Custom domain pointing to CloudFront

## API Endpoints

| Method | Endpoint                 | Purpose                         |
| ------ | ------------------------ | ------------------------------- |
| `POST` | `/api/links`             | Create a short link             |
| `GET`  | `/api/links`             | List links                      |
| `GET`  | `/api/links/{shortCode}` | View link’s metadata            |
| `GET`  | `/{shortCode}`           | Redirect to the destination URL |

Example request:

```bash
curl -X POST "\$API\_URL/api/links" \\
  -H "Content-Type: application/json" \\
  -d '{"url":"https://example.com","expiresInDays":7}'
```

## Evidence

![Infrastructure Composer Template](evidence/infrastructure-composer-template.yaml.png)
Visual representation of the SAM/CloudFormation template in Infrastructure Composer.

![SAM CloudFormation Deploy Parameters](evidence/sam-cloud-formation-deploy-parameters.png)
SAM deployment parameters entered during `sam deploy --guided`.

![SAM Deploy Change Set Confirmation](evidence/sam-deploy-change-set-confirmation.png)
CloudFormation change set review and confirmation step during deployment.

![SAM Deployment](evidence/sam-deployment.png)
Terminal output showing a successful `sam deploy` run.

![CloudFormation Outputs](evidence/cloud-formation-outputs.png)
Stack outputs after deployment, showing exported values like API URL and CloudFront domain.

![Copy Frontend Static Files to S3](evidence/copy-front-end-static-files-to-s3.png)
Uploading the static frontend files to the private S3 bucket.

![Point Custom Domain to CloudFront URL](evidence/point-custom-domain-to-cloudfront-url.png)
DNS record pointing the custom domain to the CloudFront distribution URL.

![CloudFront Custom Domain Added](evidence/cloudfront-custom-domain-added.png)
Custom domain configured as an alternate domain name in the CloudFront distribution.

![CloudFront Distribution](evidence/cloudfront-distribution.png)
CloudFront distribution overview with origin, behaviors, and status.

![CloudFront Route Domain with SSL Cert](evidence/cloudfront-route-domain-with-ssl-cert.png)
SSL/TLS certificate attached to the CloudFront distribution for HTTPS.

![Frontend Homepage](evidence/front-end-homepage.png)
The live frontend served via CloudFront showing the URL shortener UI.

![Short Link Generated](evidence/short-link-generated.png)
A short URL successfully created and displayed in the frontend.
