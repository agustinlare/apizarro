import websocket
import ssl
import logging

logging.basicConfig(format='%(asctime)s|%(levelname)s|%(message)s', level=logging.ERROR)
logging.captureWarnings(True)

msg = ''
class web_s():
    message = ''
    error = ''

def wsmessage(ws, message):
    logging.info('Message received')
    global msg

    if msg == '':
        msg = message.decode()
    else:
        msg = msg + message.decode()

    web_s.message = msg

def on_error(ws, error):
    logging.error('Error happened')
    web_s.error = error

def on_close(ws):
    logging.info("Closed ws connection")

def on_open(ws):
    logging.info('Opening ws connection to the server')

def pods_exec(cluster, ns, pod, container, exec_command):
    header = "Authorization: Bearer " + cluster['token']
    exec_command = exec_command.replace(" ", "&command=")

    if container != '':
        container = '&container=' + container
    
    url = "wss://api.%s.ar.:6443/api/v1/namespaces/%s/pods/%s/exec?command=%s&stderr=true&stdin=true&stdout=true&tty=false%s" % (cluster['prefix'], ns, pod, exec_command,container)
    logging.info("Prefix:%s Namespace: %s Pods: %s Cmd: %s Container: %s" % (cluster['prefix'], ns, pod, exec_command,container))
    
    return wsexec(url,header)

def pod_logs(cluster,ns,pod,container):

    header = "Authorization: Bearer " + cluster['token']
    container = '&container=' + container

    url = "wss://api.%s.ar.:6443/api/v1/namespaces/%s/pods/%s/log?%s" % (cluster['prefix'], ns, pod, container)
    logging.info("Prefix:%s Namespace: %s Pods: %s Container: %s" % (cluster['prefix'], ns, pod,container))

    return wsexec(url,header)
    
def wsexec(url, header):
    ws = websocket.WebSocketApp(url, on_message=wsmessage, on_error=on_error, on_close=on_close, header=[header])
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    logging.info("Socket closed data recived")    
    # Clean up global variable
    global msg
    msg = ''
    logging.info("Respond data recived")
    
    return web_s.message
