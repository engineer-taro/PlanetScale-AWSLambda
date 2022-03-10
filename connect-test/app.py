import sys
import os
import base64
import json
import boto3
import pymysql
import certifi
from botocore.exceptions import ClientError


connection = None


def get_secret():
    env = os.environ["ENV"]
    secret_name = f"{env}/planetScale"
    region_name = "ap-northeast-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e
    else:
        # Decrypts secret using the associated KMS key.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = json.loads(get_secret_value_response['SecretString'])
        else:
            secret = json.loads(
                base64.b64decode(get_secret_value_response['SecretBinary']))

    return secret


def initial_setting():
    global connection
    try:
        secret = get_secret()
        connection = pymysql.connect(
            host=secret['HOST'],
            user=secret['USERNAME'],
            passwd=secret['PASSWORD'],
            db=secret['DATABASE'],
            connect_timeout=5,
            ssl={
                'ca': certifi.where(),
                #  caファイルを配置する場合
                # 'ca': f"{os.environ['LAMBDA_TASK_ROOT']}/ca-bundle.pem",
            },
        )
    except pymysql.MySQLError as e:
        print(e)
        sys.exit()


# Lambdaハンドラー外で実行することでコネクションを使いまわせる
initial_setting()


def lambda_handler(event, context):
    global connection
    if not connection:
        connection = initial_setting()

    with connection.cursor() as cursor:
        # Read a single record
        sql = "SELECT `id`, `first_name`, `last_name` \
                FROM `users` \
                WHERE `email`=%s"
        cursor.execute(sql, ('hp@test.com',))
        result = cursor.fetchone()
        print(result)

