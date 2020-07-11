import psycopg2 as pg
import boto3
import re
import urllib.parse
import json
import os

from flask import request

from api.routes import justlooks_api
from api import utils, constants

"""
Amazon S3 with Cloudfront

https://aws.amazon.com/getting-started/hands-on/deliver-content-faster/

example image url: http://d16lddu4p1dejy.cloudfront.net/outfits/2ptDXTDdjvUGS6aULdU4ue/2ptDXTDdjvUGS6aULdU4ue-0.jpg
"""


def image_pos(image_url):
    return list(map(int, re.findall(r'-([0-9]+)', image_url)))


def get_outfit_image(outfit_id: str):
    cloudfront_url = "http://d16lddu4p1dejy.cloudfront.net/"
    s3 = boto3.resource('s3')

    outfit_images_sql = """
    SELECT * FROM public.outfit_images
    WHERE outfit_id = %s
    AND s3_path = %s
    AND pos IS NOT NULL
    """

    outfits_sql = """
    SELECT * FROM public.outfits
    WHERE outfit_id = %s
    """

    outfits_bucket = s3.Bucket('justlooks-images')
    bucket_filter = f"outfits/{outfit_id}/"
    s3_objects = outfits_bucket.objects.filter(Prefix=bucket_filter)

    max_images = 0
    for res in utils.get_source_sql_data(outfits_sql, (outfit_id,)):
        outfit = res['outfit']
        max_images = outfit['max_images']

    image_urls = [None for i in range(max_images)]

    for obj in s3_objects:
        path, filename = os.path.split(obj.key)
        if not filename:
            # Skip folders
            continue
        for res in utils.get_source_sql_data(outfit_images_sql, (outfit_id, obj.key)):
            pos = res['pos']
            print(res)
            full_url = urllib.parse.urljoin(cloudfront_url, obj.key)
            image_urls[pos] = full_url
    return image_urls

        # full_url = urllib.parse.urljoin(cloudfront_url, obj.key)
        # image_urls.append(full_url)

    #     if re.match(r'(.*)-([0-9]+|\bthumbnail\b)\.(.*)', obj.key):
    #         full_url = urllib.parse.urljoin(cloudfront_url, obj.key)
    #         image_urls.append(full_url)

    # sorted_image_urls = sorted(image_urls, key=image_pos)
    # return sorted_image_urls
    # print(sorted_image_urls)

        # print(my_bucket_object.key)
    # sql = """
    #         SELECT *
    #         FROM public.outfit_images
    #         WHERE outfit_id = %s
    #     """
    # results = get_source_sql_data(sql, (outfit_id,))

    # for result in results:
    #     image_bytes = bytes(result['image'])
    #     with open("test.jpg", 'wb') as f:
    #         f.write(image_bytes)


@justlooks_api.route("/outfit_images", methods=['GET'])
def outfit_image():
    outfit_id = request.args.get("outfit_id")
    if not outfit_id:
        return {"Error": "'outfit_id' argument is required"}

    outfit_images = get_outfit_image(outfit_id)
    return json.dumps(outfit_images)
    # return outfit_images
    # product_info = get_product(product_id)
    # return product_info
