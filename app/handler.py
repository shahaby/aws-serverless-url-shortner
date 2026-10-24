import json
import os
import secrets
import time
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError


# DynamoDB table name and public short-link domain come from Lambda environment variables.
table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
domain = os.environ["DOMAIN_NAME"]

# Allowed characters for six-character short codes.
ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def reply(status, body=None, headers=None):
    """Build an API Gateway-compatible Lambda response."""

    # JSON and CORS headers for normal API responses.
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
    }

    # Allow callers, such as redirects, to add or override headers.
    default_headers.update(headers or {})

    return {
        "statusCode": status,
        "headers": default_headers,
        "body": "" if body is None else json.dumps(body),
    }


def is_url(url):
    """Return True only for absolute HTTP or HTTPS URLs."""

    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def get_link(code):
    """Fetch a link and return None if it does not exist or has expired."""

    item = table.get_item(Key={"shortCode": code}).get("Item")

    # DynamoDB TTL deletion is asynchronous, so expiration is enforced here too.
    if not item or item.get("expiresAt", 0) < int(time.time()):
        return None

    return item


def lambda_handler(event, context):
    """Handle link creation, metadata lookup, and short-link redirects."""

    # HTTP API Gateway places method and path inside requestContext.http.
    http = event.get("requestContext", {}).get("http", {})
    method = http.get("method")
    path = http.get("path", "")

    # API Gateway supplies {shortCode} route parameters here.
    code = (event.get("pathParameters") or {}).get("shortCode")

    # POST /prod/api/links creates a new shortened URL.
    if method == "POST" and path == "/prod/api/links":
        try:
            # Parse the request JSON; use an empty object for an empty body.
            payload = json.loads(event.get("body") or "{}")
        except json.JSONDecodeError:
            return reply(400, {"message": "Request body must be valid JSON."})

        # Extract and validate the destination URL.
        url = payload.get("url", "").strip()
        if not is_url(url):
            return reply(400, {
                "message": "Provide a valid URL beginning with http:// or https://."
            })

        try:
            # Links expire in seven days by default.
            days = int(payload.get("expiresInDays", 7))

            # Keep expiry values within the supported range.
            if not 1 <= days <= 365:
                raise ValueError
        except (TypeError, ValueError):
            return reply(400, {
                "message": "expiresInDays must be an integer from 1 through 365."
            })

        # Store expiration as a Unix timestamp so DynamoDB TTL can use it.
        expires_at = int(time.time()) + days * 86400

        # Try multiple random codes in the extremely unlikely event of a collision.
        for _ in range(10):
            # Generate a cryptographically secure six-character code.
            code = "".join(secrets.choice(ALPHABET) for _ in range(6))

            # This is the complete DynamoDB record for a short link.
            item = {
                "shortCode": code,
                "destinationUrl": url,
                "expiresAt": expires_at,
                "clickCount": 0,
            }

            try:
                # Create the item only if another request has not used this code.
                table.put_item(
                    Item=item,
                    ConditionExpression="attribute_not_exists(shortCode)",
                )

                # Return the newly created short URL.
                return reply(201, {
                    "shortCode": code,
                    "shortUrl": f"https://{domain}/{code}",
                    "destinationUrl": url,
                    "expiresAt": expires_at,
                })

            except ClientError as error:
                # A code collision is safe to retry; other DynamoDB failures are not.
                if error.response["Error"]["Code"] != "ConditionalCheckFailedException":
                    raise

        # Ten collisions means creation failed, even though it is very unlikely.
        return reply(500, {
            "message": "Could not create a unique code. Please try again."
        })

    # GET /api/links/{shortCode} returns metadata, useful for testing or admin views.
    if method == "GET" and path.startswith("/api/links/"):
        if not code:
            return reply(400, {"message": "Missing short code."})

        item = get_link(code)
        if not item:
            return reply(404, {"message": "Short link not found or expired."})

        return reply(200, {
            "shortCode": item["shortCode"],
            "destinationUrl": item["destinationUrl"],
            "expiresAt": item["expiresAt"],
            "clickCount": item.get("clickCount", 0),
        })

    # GET /{shortCode} redirects the visitor to its stored destination.
    if method == "GET" and code:
        item = get_link(code)
        if not item:
            return reply(404, {"message": "Short link not found or expired."})

        # Atomically increment the click count without reading and rewriting it.
        table.update_item(
            Key={"shortCode": code},
            UpdateExpression="ADD clickCount :n",
            ExpressionAttributeValues={":n": 1},
        )

        # Send a temporary redirect and prevent clients from caching it.
        return reply(302, None, {
            "Location": item["destinationUrl"],
            "Cache-Control": "no-store",
        })

    # Every other route returns a JSON 404 response.
    return reply(404, {"message": f"Route not found. Path: {path}"})