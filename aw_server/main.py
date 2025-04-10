import logging
import sys

from aw_core.log import setup_logging
from aw_datastore import get_storage_methods

from . import __version__
from .config import config
from .server import _start

logger = logging.getLogger(__name__)


def main():
    """Called from the executable and __main__.py"""

    settings, storage_method = parse_settings()

    # FIXME: The LogResource API endpoint relies on the log being in JSON format
    # at the path specified by aw_core.log.get_log_file_path(). We probably want
    # to write the LogResource API so that it does not depend on any physical file
    # but instead add a logging handler that it can use privately.
    # That is why log_file_json=True currently.
    # UPDATE: The LogResource API is no longer available so log_file_json is now False.
    setup_logging(
        "aw-server",
        testing=settings.testing,
        verbose=settings.verbose,
        log_stderr=True,
        log_file=True,
)
   # ========== 新增两行日志 ==========
    from aw_server.server import app_folder, static_folder  # 从 server.py 导入路径
    logger.info(f"App folder: {app_folder}")  # 打印模块路径
    logger.info(f"Static folder: {static_folder}")  # 打印静态文件目录
    # ==================================
    logger.info(f"Using storage method: {settings.storage}")

    if settings.testing:
        logger.info("Will run in testing mode")

    if settings.custom_static:
        logger.info(f"Using custom_static: {settings.custom_static}")

    logger.info("Starting up1...")
    _start(
        host=settings.host,
        port=settings.port,
        testing=settings.testing,
        storage_method=storage_method,
        cors_origins=settings.cors_origins,
        custom_static=settings.custom_static,
    )


def parse_settings():
    import argparse

    """ CLI Arguments """
    parser = argparse.ArgumentParser(description="Starts an ActivityWatch server")
    parser.add_argument(
        "--testing",
        action="store_true",
        help="Run aw-server in testing mode using different ports and database",
    )
    parser.add_argument("--verbose", action="store_true", help="Be chatty.")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and quit",
    )
    parser.add_argument(
        "--log-json", action="store_true", help="Output the logs in JSON format"
    )
    parser.add_argument(
        "--host", dest="host", help="Which host address to bind the server to"
    )
    parser.add_argument(
        "--port", dest="port", type=int, help="Which port to run the server on"
    )
    parser.add_argument(
        "--storage",
        dest="storage",
        help="The method to use for storing data. Some methods (such as MongoDB) require specific Python packages to be available (in the MongoDB case: pymongo)",
    )
    parser.add_argument(
        "--cors-origins",
        dest="cors_origins",
        help="CORS origins to allow (as a comma separated list)",
    )
    parser.add_argument(
        "--custom-static",
        dest="custom_static",
        help="The custom static directories. Format: watcher_name=path,watcher_name2=path2,...",
    )
    args = parser.parse_args()
    if args.version:
        print(__version__)
        sys.exit(0)

    """ Parse config file """
    configsection = "server" if not args.testing else "server-testing"
    settings = argparse.Namespace()
    settings.host = config[configsection]["host"]
    settings.port = int(config[configsection]["port"])
    settings.storage = config[configsection]["storage"]
    settings.cors_origins = config[configsection]["cors_origins"]
    settings.custom_static = dict(config[configsection]["custom_static"])

    """ If a argument is not none, override the config value """
    for key, value in vars(args).items():
        if value is not None:
            if key == "custom_static":
                settings.custom_static = parse_str_to_dict(value)
            else:
                vars(settings)[key] = value

    settings.cors_origins = [o for o in settings.cors_origins.split(",") if o]

    storage_methods = get_storage_methods()
    storage_method = storage_methods[settings.storage]

    return settings, storage_method


def parse_str_to_dict(str_value):
    """Parses a dict from a string in format: key=value,key2=value2,..."""
    output = dict()
    key_value_pairs = str_value.split(",")

    for pair in key_value_pairs:
        pair_split = pair.split("=")

        if len(pair_split) != 2:
            raise ValueError(f"Cannot parse key value pair: {pair}")

        key, value = pair_split
        output[key] = value

    return output
