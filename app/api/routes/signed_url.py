import boto3
from flask import request
from webargs.flaskparser import use_kwargs
from webargs import fields

from app.api import api_bp

# https://github.com/PostgREST/postgrest/issues/171
# https://devcenter.heroku.com/articles/s3-upload-python
# Solution 1:
# Make a route that returns a signed URL that can be used to upload a file to S3 bucket.
# Solution 2: (This seems difficult, also im already using Flask)
# Make a postgres function that returns a signed URL that can be used to upload a file to S3 bucket.
#
# Finally:
# Front end must Send actual file to S3 using signed URL and send s3 details to postgres.

file_args = {
    "file_name": fields.Str(required=True),
    "mime_type": fields.Str(required=True),
}


@api_bp.route('/create_signed_s3_url', methods=['GET'])
@use_kwargs(file_args, location="querystring")  # Injects keyword arguments
def create_signed_s3_url(file_name: str, mime_type: str):
    s3_bucket = "justlooks-images"
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#shared-credentials-file
    session = boto3.Session(profile_name="direct-upload-s3")
    s3_client = session.client("s3")

    presigned_post = s3_client.generate_presigned_post(
        Bucket=s3_bucket,
        Key=f"outfits/{file_name}",
        Fields={
            "acl": "public-read",
            "Content-Type": mime_type
        },
        Conditions=[
            {"acl": "public-read"},
            {"Content-Type": mime_type}
        ],
        ExpiresIn=3600
    )
    # print(presigned_post)
    # WEBSITE PERMISSION
    # https://docs.aws.amazon.com/AmazonS3/latest/dev/WebsiteAccessPermissionsReqd.htmls
    # GOOD EXAMPLE OF PERMISSION
    # https://docs.aws.amazon.com/AmazonS3/latest/dev/example-walkthroughs-managing-access-example1.html
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html#generating-a-presigned-url-to-upload-a-file
    return presigned_post
