import os
import sys


try:
    current_path = sys.path[0] if sys.path else ''
    new_path = os.path.join(os.path.dirname(current_path)) if current_path else '/dinasore'
    
    sys.path.append(new_path)
        
except Exception as e:
    print("Path error:", e)


from core import logging
from communication import tcp_server
from core import manager

# from netconf.connect import wifi_connect


def parse_arguments():
    defaults = {
        'address': 'localhost',
        'port_diac': 61499,
        'log_level': 'ERROR'
    }
    args = sys.argv[1:]
    
    i = 0
    while i < len(args):
        if args[i] == '-a' and i + 1 < len(args):
            defaults['address'] = args[i + 1]
            i += 2
        elif args[i] == '-p' and i + 1 < len(args):
            try:
                defaults['port_diac'] = int(args[i + 1])
            except ValueError:
                print(f"Port value must be numeric: {args[i + 1]}")
            i += 2
        elif args[i] == '-l' and i + 1 < len(args):
            defaults['log_level'] = args[i + 1]
            i += 2
        else:
            print(f"Unknown arg: {args[i]}")
            i += 1
    
    return defaults

if __name__ == "__main__":
    
    # address = wifi_connect()
    address = "localhost"
    
    log_levels = {'ERROR': logging.ERROR,
                  'WARN': logging.WARN,
                  'INFO': logging.INFO,
                  'DEBUG': logging.DEBUG}
    if address == None:
        address = 'localhost'
    diac_address = None
    project_name = None
    port_diac = 61499
    port_opc = 4840
    log_level = log_levels['ERROR']
    n_samples = 10
    secs_sample = 20
    monitor = [n_samples, secs_sample]
    agent = False

    help_message = "Usage: python core/main.py [ARGS]\n\n" \
                   " -h, --help: display the help message\n" \
                   " -a, --address: ip address to bind at (default: localhost)\n" \
                   " -p, --port_diac: port for the 4diac communication (default: 61499)\n" \
                   " -l, --log_level: logging level at the file resources/error_list.log\n" \
                   "                  INFO, WARN or ERROR (default: ERROR)"

    # build parser for application command line arguments
    args = parse_arguments()

    if args['port_diac'] != None: port_diac = args['port_diac']
    if args['log_level'] != None: log_level = log_levels[args['log_level']]

    # Configure the logging output
    log_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'error_list.log')
    try:
        os.remove(log_path)
    except:
        pass
    logging.basicConfig(filename=log_path,
                        level=log_level,
                        format='[%(asctime)s][%(levelname)s][%(threadName)s] %(message)s')

    # creates the 4diac manager
    m = manager.Manager()
    # sets the ua integration option
    m.build_fboot()
    # creates the tcp server to communicate with the 4diac
    hand = tcp_server.TcpServer(address, port_diac, 10, m)
    try:
        # handles every client
        while True:
            hand.handle_client()
    except KeyboardInterrupt:
        logging.info('interrupted server')
        m.stop()
        hand.stop_server()
        sys.exit(0)
