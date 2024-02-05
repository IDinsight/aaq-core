import os
import re
import urllib.parse


# from https://stackoverflow.com/a/66572093/7664921
def get_cloud_watch_log_stream_url(
    log_group: str,
    log_stream: str,
    region: str,
) -> str:
    """Return a properly formatted url string for cloud watch logs"""

    url = f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}"

    def aws_encode(value: str) -> str:
        """The heart of this is that AWS likes to quote things twice with some
        substitution"""
        value = urllib.parse.quote_plus(value)
        value = re.sub(r"\+", " ", value)
        return re.sub(r"%", "$", urllib.parse.quote_plus(value))

    bookmark = "#logsV2:log-groups"
    bookmark += "/log-group/" + aws_encode(log_group)
    bookmark += "/log-events/" + log_stream

    return url + bookmark


if __name__ == "__main__":
    log_group = os.getenv("LOG_GROUP", "")
    log_stream = os.getenv("LOG_STREAM", "")
    region = os.getenv("AWS_REGION", "")
    print(get_cloud_watch_log_stream_url(log_group, log_stream, region))
