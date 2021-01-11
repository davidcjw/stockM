import logging
import boto3

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_portfolios():
    s3 = boto3.client('s3', region_name='ap-southeast-1')
    try:
        s3.download_file(
            Filename='conversationbot',
            Bucket='stockm-yfinance',
            Key='conversationbot'
        )
        logger.info("Downloaded portfolios from s3!")
    except Exception as e:
        logger.info(e)
