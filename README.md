# aws-serverless-url-shortner
A serverless web app for creating short URLs. CloudFront securly (https) and quickly (CDN) serves the static frontend from a private S3 Bucket. API calls made through API Gateway and served by Lambda function(s) providing a robust and secure backend while DynamoDB stores records of links.
