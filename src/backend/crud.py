import hashlib
import numpy as np
from typing import List, Dict, Optional
from backend.database import get_db_connection, get_db_cursor

# Import Subgraph Algorithmus aus dem hjstephan/subgraph Package
try:
    from subgraph import Subgraph
    SUBGRAPH_AVAILABLE = True
except ImportError:
    print("WARNING: Subgraph package not available. Install with: pip install git+https://github.com/hjstephan/subgraph.git")
    SUBGRAPH_AVAILABLE = False

if SUBGRAPH_AVAILABLE:
    comparator = Subgraph()

def compute_signatures(matrix: np.ndarray) -> List[int]:
    """Berechnet Spalten-Signaturen fuer Adjacency Matrix"""
    n = matrix.shape[0]
    signatures = []
    for col in range(n):
        row_sig = sum(2**i for i in range(n) if matrix[i, col] == 1)
        col_weight = col * (2**n)
        signatures.append(row_sig + col_weight)
    return signatures

def compute_signature_hash(signatures: List[int]) -> str:
    """Berechnet SHA-256 Hash der Signatur-Sequenz"""
    sig_str = str(signatures).encode()
    return hashlib.sha256(sig_str).hexdigest()

def create_network(name: str, network_type: str, organism: str,
                   description: str, node_labels: List[str],
                   adjacency_matrix: List[List[int]]) -> Dict:
    """Erstellt neues biologisches Netzwerk"""
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)

        matrix_np = np.array(adjacency_matrix, dtype=int)
        node_count = len(node_labels)
        edge_count = int(np.sum(matrix_np))

        signatures = compute_signatures(matrix_np)
        sig_hash = compute_signature_hash(signatures)

        cursor.execute("""
            INSERT INTO biological_networks
            (name, network_type, organism, description, node_count, edge_count)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING network_id
        """, (name, network_type, organism, description, node_count, edge_count))

        network_id = cursor.fetchone()['network_id']

        cursor.execute("""
            INSERT INTO network_matrices
            (network_id, node_labels, adjacency_matrix, signature_array, signature_hash)
            VALUES (%s, %s, %s, %s, %s)
        """, (network_id, node_labels, adjacency_matrix, signatures, sig_hash))

        return {
            'network_id': network_id,
            'name': name,
            'node_count': node_count,
            'edge_count': edge_count,
            'signature_hash': sig_hash
        }

def get_all_networks(limit: int = 33, random_sample: bool = True) -> List[Dict]:
    """
    Holt Netzwerke aus der DB
    
    Args:
        limit: Maximale Anzahl zurückgegebener Netzwerke (default: 33)
        random_sample: Wenn True, werden zufällige Netzwerke geladen (default: True)
    
    Returns:
        Liste von Netzwerk-Dictionaries
    """
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        
        if random_sample:
            # Lade 33 zufällige Netzwerke mit TABLESAMPLE
            # TABLESAMPLE SYSTEM ist sehr schnell, auch bei Millionen Zeilen
            cursor.execute(f"""
                SELECT bn.*, nm.node_labels, nm.signature_hash
                FROM biological_networks bn
                LEFT JOIN network_matrices nm ON bn.network_id = nm.network_id
                ORDER BY RANDOM()
                LIMIT %s
            """, (limit,))
        else:
            # Lade neueste Netzwerke
            cursor.execute(f"""
                SELECT bn.*, nm.node_labels, nm.signature_hash
                FROM biological_networks bn
                LEFT JOIN network_matrices nm ON bn.network_id = nm.network_id
                ORDER BY bn.created_at DESC
                LIMIT %s
            """, (limit,))
        
        return cursor.fetchall()

def get_network_by_id(network_id: int) -> Optional[Dict]:
    """Holt spezifisches Netzwerk mit Matrix"""
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute("""
            SELECT bn.*, nm.node_labels, nm.adjacency_matrix, nm.signature_array
            FROM biological_networks bn
            JOIN network_matrices nm ON bn.network_id = nm.network_id
            WHERE bn.network_id = %s
        """, (network_id,))
        return cursor.fetchone()

def search_subgraph(query_matrix: List[List[int]],
                    query_labels: List[str]) -> List[Dict]:
    """Sucht in DB nach Netzwerken, die query_matrix enthalten koennten."""
    if not SUBGRAPH_AVAILABLE:
        return [{
            'error': 'Subgraph package not installed',
            'message': 'Install with: pip install git+https://github.com/hjstephan/subgraph.git'
        }]

    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)

        query_np = np.array(query_matrix, dtype=int)
        query_node_count = query_np.shape[0]
        query_edge_count = int(np.sum(query_np))

        cursor.execute("""
            SELECT bn.network_id, bn.name, bn.network_type, bn.organism,
                   bn.node_count, bn.edge_count,
                   nm.node_labels, nm.adjacency_matrix
            FROM biological_networks bn
            JOIN network_matrices nm ON bn.network_id = nm.network_id
            WHERE bn.node_count >= %s AND bn.edge_count >= %s
            ORDER BY bn.node_count ASC
        """, (query_node_count, query_edge_count))

        candidates = cursor.fetchall()

        print(f"Subgraph-Suche: {len(candidates)} Kandidaten fuer Query (n={query_node_count}, e={query_edge_count})")

        matches = []
        for candidate in candidates:
            candidate_matrix = np.array(candidate['adjacency_matrix'], dtype=int)

            result = comparator.compare_graphs(query_np, candidate_matrix)
            decision = result[0] if isinstance(result, tuple) else result

            if decision in ['keep_B', 'keep_both']:
                match_type = 'exact' if decision == 'keep_both' else 'subgraph'
                matches.append({
                    'network_id': candidate['network_id'],
                    'name': candidate['name'],
                    'network_type': candidate['network_type'],
                    'organism': candidate['organism'],
                    'node_labels': candidate['node_labels'],
                    'node_count': candidate['node_count'],
                    'edge_count': candidate['edge_count'],
                    'match_type': match_type,
                    'subgraph_result': decision
                })
            #    print(f"  Match: {candidate['name']} ({decision})")
            # else:
            #    print(f"  No match: {candidate['name']} ({decision})")

        print(f"Gefunden: {len(matches)} Matches")
        return matches

def delete_network(network_id: int) -> bool:
    """Loescht Netzwerk aus DB (CASCADE loescht auch Matrix)"""
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute("""
            DELETE FROM biological_networks WHERE network_id = %s
            RETURNING network_id
        """, (network_id,))
        return cursor.fetchone() is not None