import socket
import threading
import sys
import time

# thread worker
def worker(host_ip, ports, state, lock, open_ports, timeout):
    while True:
        # get next port safely
        with lock:
            if state['index'] >= len(ports):
                return
            port = ports[state['index']]
            state['index'] += 1
            done = state['index']
            total = len(ports)

        # try connecting to the port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            if s.connect_ex((host_ip, port)) == 0:
                # found open port
                with lock:
                    open_ports.append(port)
        except Exception:
            pass  # ignore
        finally:
            s.close()

        # Progress
        if done % max(1, total // 100) == 0 or done <= 50:
            print(f"[{done}/{total}] checked...", end="\r", flush=True)

# input prompt
def prompt(prompt_text, default=None):
    v = input(f"{prompt_text}" + (f" [{default}]" if default is not None else "") + ": ").strip()
    return v if v != "" else default

# main program logic
def main():
    print("Simple Port Scanner.")
    print("WARNING: Only scan systems you own or have permission to test.\n")

    # get and resolve host
    host = prompt("Host (hostname or IP)", "localhost")
    try:
        host_ip = socket.gethostbyname(host)
    except Exception as e:
        print(f"Cannot resolve host '{host}': {e}", file=sys.stderr)
        sys.exit(2)

    # port range input
    start = int(prompt("Start port", "1"))
    end = int(prompt("End port", "1024"))
    if start < 1 or end > 65535 or start > end:
        print("Invalid port range.", file=sys.stderr)
        sys.exit(1)

    # thread and timeout settings
    threads_count = int(prompt("Threads", "100"))
    timeout_ms = int(prompt("Timeout (ms)", "800"))
    timeout = timeout_ms / 1000.0

    # initialize data structures
    ports = list(range(start, end + 1))
    open_ports = []
    lock = threading.Lock()
    state = {'index': 0}

    # start scan
    print(f"\nScanning {host} ({host_ip}) ports {start}-{end} with {threads_count} threads, timeout={timeout}s\n")
    t0 = time.time()

    threads = []
    for _ in range(min(threads_count, len(ports))):
        t = threading.Thread(target=worker, args=(host_ip, ports, state, lock, open_ports, timeout), daemon=True)
        threads.append(t)
        t.start()

    # wait for threads to finish
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\nScan interrupted by user.")
        sys.exit(130)

    # show results
    elapsed = time.time() - t0
    print()

    open_ports.sort()
    if open_ports:
        print(f"Open ports ({len(open_ports)}) found in {elapsed:.2f}s:")
        for p in open_ports:
            print(f"  - {p}")
    else:
        print(f"No open ports detected in the specified range (scanned {len(ports)} ports in {elapsed:.2f}s).")

# entry point
if __name__ == "__main__":
    main()
