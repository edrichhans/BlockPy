import socket, os, errno, logmatic, logging

# Setup logging
try:
    os.makedirs('logs')
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

logger = logging.getLogger()
handler = logging.FileHandler('logs/peer.log')
handler.setFormatter(logmatic.JsonFormatter(extra={"hostname":socket.gethostname()}))
 
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def setFilename(filename):
    global logger
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.FileHandler('logs/' + filename)
    handler.setFormatter(logmatic.JsonFormatter(extra={"hostname":socket.gethostname()}))

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger