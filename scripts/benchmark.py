"""
Multithreading Benchmark & Monitoring Script
Run this to generate performance graphs for your report
Usage: python scripts/benchmark.py
"""
import threading
import time
import requests
import json
import os

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Note: matplotlib not installed. Install with: pip install matplotlib")

BASE_URL = "http://localhost"
SERVICES = {
    'Auth':         f'{BASE_URL}:5001',
    'Registration': f'{BASE_URL}:5002',
    'LMS':          f'{BASE_URL}:5003',
    'Result':       f'{BASE_URL}:5004',
}

# ─── TEST 1: Health Check All Services ────────────────────────────────────────
def test_all_health():
    print("\n=== Health Check ===")
    for name, url in SERVICES.items():
        try:
            r = requests.get(f"{url}/health", timeout=3)
            print(f"  ✅ {name}: {r.json()['status']}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")

# ─── TEST 2: Single vs Multi-thread Benchmark ──────────────────────────────
def benchmark_threading():
    print("\n=== Threading Benchmark ===")
    url = f"{BASE_URL}:5001/health"
    thread_counts = [1, 5, 10, 25, 50]
    results = {}

    for n in thread_counts:
        times = []
        lock = threading.Lock()

        def make_request():
            start = time.time()
            try:
                requests.get(url, timeout=5)
                elapsed = (time.time() - start) * 1000
                with lock:
                    times.append(elapsed)
            except:
                pass

        start_total = time.time()
        threads = [threading.Thread(target=make_request) for _ in range(n)]
        for t in threads: t.start()
        for t in threads: t.join()
        total = (time.time() - start_total) * 1000

        avg = sum(times) / len(times) if times else 0
        results[n] = {'total_ms': round(total, 1), 'avg_ms': round(avg, 1)}
        print(f"  {n:3d} threads → total: {total:7.1f}ms  avg/req: {avg:6.1f}ms")

    return results

# ─── TEST 3: Socket Communication ─────────────────────────────────────────────
def test_socket_communication():
    print("\n=== Distributed Socket Communication ===")
    import socket
    socket_ports = {'Auth': 6001, 'Registration': 6002, 'LMS': 6003, 'Result': 6004}
    for name, port in socket_ports.items():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect(('localhost', port))
            s.send(b"PING")
            resp = s.recv(1024).decode()
            s.close()
            print(f"  ✅ {name} socket: {resp}")
        except Exception as e:
            print(f"  ❌ {name} socket (port {port}): {e}")

# ─── GENERATE GRAPHS ──────────────────────────────────────────────────────────
def generate_graphs(thread_results):
    if not HAS_MATPLOTLIB:
        print("\nSkipping graphs - matplotlib not available")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('University Distributed System - Performance Benchmark', fontsize=14, fontweight='bold')

    x = list(thread_results.keys())
    total_times = [thread_results[n]['total_ms'] for n in x]
    avg_times   = [thread_results[n]['avg_ms'] for n in x]

    # Graph 1: Total execution time vs thread count
    axes[0].bar(x, total_times, color='steelblue', alpha=0.8, edgecolor='black')
    axes[0].set_xlabel('Number of Concurrent Threads')
    axes[0].set_ylabel('Total Execution Time (ms)')
    axes[0].set_title('Total Time vs Concurrent Users')
    axes[0].grid(axis='y', alpha=0.5)
    for i, (n, v) in enumerate(zip(x, total_times)):
        axes[0].text(n, v + 2, f'{v:.0f}ms', ha='center', fontsize=9)

    # Graph 2: Avg response time
    axes[1].plot(x, avg_times, marker='o', color='coral', linewidth=2, markersize=8)
    axes[1].fill_between(x, avg_times, alpha=0.2, color='coral')
    axes[1].set_xlabel('Number of Concurrent Threads')
    axes[1].set_ylabel('Average Response Time per Request (ms)')
    axes[1].set_title('Avg Response Time vs Load')
    axes[1].grid(alpha=0.5)

    plt.tight_layout()
    graph_path = 'benchmark_results.png'
    plt.savefig(graph_path, dpi=150, bbox_inches='tight')
    print(f"\n  📊 Graph saved to: {graph_path}")
    plt.close()

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════╗")
    print("║  University System — Benchmark & Monitor      ║")
    print("╚══════════════════════════════════════════════╝")

    test_all_health()
    thread_results = benchmark_threading()
    test_socket_communication()
    generate_graphs(thread_results)

    print("\n✅ Benchmark complete!")
    print("\nFor live monitoring, run in separate terminals:")
    print("  docker stats")
    print("  kubectl top pods -n university")
