#!/usr/bin/env python3
"""
Load Test für gen-db API

Testet:
- Sequenzielle vs parallele Performance
- Netzwerk-Erstellung unter Last
- Subgraph-Suche unter Last
- Parallelisierungs-Effekt

Usage:
    python load_test.py --host http://localhost:8000 --concurrent 10 --count 100
"""

import asyncio
import aiohttp
import time
import json
import sys
import argparse
from typing import List, Tuple
from statistics import mean, stdev
import random


class LoadTester:
    """API Load Tester mit asyncio"""
    
    def __init__(self, base_url: str, concurrent: int = 4):
        self.base_url = base_url.rstrip('/')
        self.concurrent = concurrent
        self.results = []
        
    async def create_network(self, session: aiohttp.ClientSession, index: int) -> Tuple[float, bool]:
        """Erstelle ein Netzwerk und messe Zeit"""
        url = f"{self.base_url}/api/networks"
        
        # Generiere zufälliges Netzwerk
        n = random.randint(3, 8)
        node_labels = [f"Node_{i}" for i in range(n)]
        adjacency_matrix = [
            [random.randint(0, 1) if i != j else 0 for j in range(n)]
            for i in range(n)
        ]
        
        payload = {
            "name": f"Network_{index}",
            "network_type": "test",
            "organism": "test",
            "description": f"Auto-generated test network {index}",
            "node_labels": node_labels,
            "adjacency_matrix": adjacency_matrix
        }
        
        start = time.perf_counter()
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                elapsed = time.perf_counter() - start
                success = resp.status == 200
                data = await resp.json()
                return elapsed, success
        except Exception as e:
            print(f"Error creating network {index}: {e}")
            return time.perf_counter() - start, False
    
    async def search_subgraph(self, session: aiohttp.ClientSession, index: int) -> Tuple[float, bool, int]:
        """Suche Subgraph und messe Zeit"""
        url = f"{self.base_url}/api/networks/search"
        
        # Zufälliger Suchgraph
        n = random.randint(2, 4)
        node_labels = [f"Query_{i}" for i in range(n)]
        adjacency_matrix = [
            [random.randint(0, 1) if i != j else 0 for j in range(n)]
            for i in range(n)
        ]
        
        payload = {
            "node_labels": node_labels,
            "adjacency_matrix": adjacency_matrix
        }
        
        start = time.perf_counter()
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                elapsed = time.perf_counter() - start
                success = resp.status == 200
                data = await resp.json()
                matches = len(data.get("data", [])) if success else 0
                return elapsed, success, matches
        except Exception as e:
            print(f"Error searching subgraph {index}: {e}")
            return time.perf_counter() - start, False, 0
    
    async def run_concurrent_creates(self, count: int) -> List[float]:
        """Führe konzurrent mehrere Netzwerk-Erstellungen durch"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.create_network(session, i)
                for i in range(count)
            ]
            
            results = []
            for i in range(0, count, self.concurrent):
                batch = tasks[i:i+self.concurrent]
                batch_results = await asyncio.gather(*batch)
                results.extend(batch_results)
                
                # Progress
                progress = min(i + self.concurrent, count)
                print(f"  Progress: {progress}/{count}", end='\r')
            
            print()
            return [r[0] for r in results if r[1]]  # Nur erfolgreiche
    
    async def run_concurrent_searches(self, count: int) -> Tuple[List[float], int]:
        """Führe konzurrent mehrere Subgraph-Suchen durch"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.search_subgraph(session, i)
                for i in range(count)
            ]
            
            results = []
            total_matches = 0
            
            for i in range(0, count, self.concurrent):
                batch = tasks[i:i+self.concurrent]
                batch_results = await asyncio.gather(*batch)
                results.extend(batch_results)
                total_matches += sum(r[2] for r in batch_results if r[1])
                
                # Progress
                progress = min(i + self.concurrent, count)
                print(f"  Progress: {progress}/{count}", end='\r')
            
            print()
            return [r[0] for r in results if r[1]], total_matches  # Nur erfolgreiche
    
    async def health_check(self) -> bool:
        """Überprüfe API Health"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/api/health") as resp:
                    return resp.status == 200
            except Exception as e:
                print(f"Health check failed: {e}")
                return False


def print_stats(name: str, times: List[float]):
    """Drucke Statistiken"""
    if not times:
        print(f"  {name}: No successful requests")
        return
    
    min_time = min(times)
    max_time = max(times)
    avg_time = mean(times)
    std_time = stdev(times) if len(times) > 1 else 0
    
    print(f"  {name}:")
    print(f"    Min:     {min_time*1000:.2f}ms")
    print(f"    Max:     {max_time*1000:.2f}ms")
    print(f"    Avg:     {avg_time*1000:.2f}ms")
    print(f"    StdDev:  {std_time*1000:.2f}ms")
    print(f"    Count:   {len(times)}")
    print(f"    RPS:     {len(times) / sum(times):.2f} req/s")


async def main():
    parser = argparse.ArgumentParser(description='Gen-DB API Load Test')
    parser.add_argument('--host', default='http://localhost:8000', help='API base URL')
    parser.add_argument('--concurrent', type=int, default=4, help='Number of concurrent requests')
    parser.add_argument('--creates', type=int, default=20, help='Number of network creates to test')
    parser.add_argument('--searches', type=int, default=30, help='Number of subgraph searches to test')
    
    args = parser.parse_args()
    
    tester = LoadTester(args.host, args.concurrent)
    
    print(f"Gen-DB Load Test")
    print(f"  Host: {args.host}")
    print(f"  Concurrent: {args.concurrent}")
    print()
    
    # Health Check
    print("Checking API health...")
    healthy = await tester.health_check()
    if not healthy:
        print("ERROR: API is not healthy!")
        sys.exit(1)
    print("✓ API is healthy")
    print()
    
    # Create Networks Test
    print(f"Testing {args.creates} concurrent network creations...")
    start = time.perf_counter()
    create_times = await tester.run_concurrent_creates(args.creates)
    create_total = time.perf_counter() - start
    print()
    print(f"Network Creation Test (Total time: {create_total:.2f}s)")
    print_stats("Create Times", create_times)
    print()
    
    # Search Networks Test
    print(f"Testing {args.searches} concurrent subgraph searches...")
    start = time.perf_counter()
    search_times, total_matches = await tester.run_concurrent_searches(args.searches)
    search_total = time.perf_counter() - start
    print()
    print(f"Subgraph Search Test (Total time: {search_total:.2f}s)")
    print_stats("Search Times", search_times)
    print(f"  Total Matches: {total_matches}")
    print()
    
    # Parallelisierungs-Analyse
    print("Parallelization Analysis:")
    if search_times:
        sequential_time = sum(search_times)
        parallel_time = search_total
        speedup = sequential_time / parallel_time
        efficiency = speedup / args.concurrent
        
        print(f"  Sequential Estimate: {sequential_time:.2f}s")
        print(f"  Parallel Actual:     {parallel_time:.2f}s")
        print(f"  Speedup:             {speedup:.2f}x")
        print(f"  Efficiency:          {efficiency*100:.1f}%")
        
        if efficiency > 0.7:
            print("  Status: ✓ Good parallelization")
        elif efficiency > 0.4:
            print("  Status: ⚠ Moderate parallelization")
        else:
            print("  Status: ✗ Poor parallelization")
    print()


if __name__ == '__main__':
    asyncio.run(main())
