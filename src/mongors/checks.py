import gevent.pool
import gevent.socket


def wait_for_instance(address, port=None, timeout=10.0, register_state=None):
    """Loop until timeout and check for receiving socket."""

    if port is None:
        port = 27017

    timer = gevent.Timeout(timeout)
    timer.start()

    try:
        while True:
            socket = gevent.socket.socket()
            try:
                socket.connect((address, port))
                if callable(register_state):
                    register_state((address, port), True)
                return True

            except gevent.socket.error:
                gevent.sleep(0.1)


    except gevent.Timeout:
        if callable(register_state):
            register_state((address, port), False)

        return False

    finally:
        timer.cancel()


def wait_for_instances(*instances, **kwargs):
    """spawn x greenlets and wait for them."""

    timeout = kwargs.get("timeout", 10.0)

    states = {
        True: [],
        False: []
    }

    def register_state(addr_port, state):
        states[state].append(addr_port)

    pool = gevent.pool.Pool(len(instances))
    for address, port in instances:
        pool.spawn(wait_for_instance,
                   address=address, port=port, timeout=timeout, register_state=register_state)

    try:
        pool.join()
    except gevent.Timeout:
        pass

    return states
