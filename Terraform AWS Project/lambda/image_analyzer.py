import json
import boto3
import base64

rekognition = boto3.client("rekognition")
bedrock_runtime = boto3.client("bedrock-runtime")


def lambda_handler(event, context):
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST"
    }

    try:
        body = json.loads(event.get("body", "{}"))
        image_base64 = body.get("image")

        if not image_base64:
            return {
                "statusCode": 400,
                "headers": cors_headers,
                "body": json.dumps({"error": "No image provided"})
            }

        image_bytes = base64.b64decode(image_base64)

        rekognition_response = rekognition.detect_labels(
            Image={"Bytes": image_bytes},
            MaxLabels=10,
            MinConfidence=80
        )

        labels = [label["Name"] for label in rekognition_response["Labels"]]

        if not labels:
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({
                    "labels": [],
                    "description": "No labels detected."
                })
            }

        prompt = (
            f"Based on these labels: {', '.join(labels)}. "
            f"Generate one clear and natural English sentence describing the image."
        )

        bedrock_response = bedrock_runtime.converse(
            modelId="deepseek.v3.2",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            inferenceConfig={
                "maxTokens": 100,
                "temperature": 0.5,
                "topP": 0.9
            }
        )

        description = (
            bedrock_response["output"]["message"]["content"][0]["text"].strip()
        )

        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({
                "labels": labels,
                "description": description
            })
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({
                "error": str(e)
            })
        }