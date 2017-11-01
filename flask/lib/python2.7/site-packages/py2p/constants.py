protocol_version = "0.7"
node_policy_version = "870"

version = '.'.join((protocol_version, node_policy_version))

__version__ = version  # type: str
version_info = tuple(map(int, __version__.split(".")))  # type: Tuple[int, ...]
