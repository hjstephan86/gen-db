import logging
import hashlib
import numpy as np
from typing import List, Dict, Optional
from .database import get_db_connection, get_db_cursor
from .subgraph_executor import compare_graphs_async

logger = logging.getLogger(__name__)

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
    logger.info(f"create_network: name={name} type={network_type} organism={organism}")
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

        logger.info(f"create_network: Created network_id={network_id} nodes={node_count} edges={edge_count}")
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
    logger.info(f"get_all_networks: limit={limit} random_sample={random_sample}")
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)

        if random_sample:
            cursor.execute(f"""
                SELECT bn.*, nm.node_labels, nm.signature_hash
                FROM biological_networks bn
                LEFT JOIN network_matrices nm ON bn.network_id = nm.network_id
                ORDER BY RANDOM()
                LIMIT %s
            """, (limit,))
        else:
            cursor.execute(f"""
                SELECT bn.*, nm.node_labels, nm.signature_hash
                FROM biological_networks bn
                LEFT JOIN network_matrices nm ON bn.network_id = nm.network_id
                ORDER BY bn.created_at DESC
                LIMIT %s
            """, (limit,))

        results = cursor.fetchall()
        logger.info(f"get_all_networks: Fetched {len(results)} records")
        return results

def get_network_by_id(network_id: int) -> Optional[Dict]:
    """Holt spezifisches Netzwerk mit Matrix"""
    logger.info(f"get_network_by_id: network_id={network_id}")
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute("""
            SELECT bn.*, nm.node_labels, nm.adjacency_matrix, nm.signature_array
            FROM biological_networks bn
            JOIN network_matrices nm ON bn.network_id = nm.network_id
            WHERE bn.network_id = %s
        """, (network_id,))
        result = cursor.fetchone()
        if result:
            logger.info(f"get_network_by_id: Found network '{result['name']}'")
        else:
            logger.warning(f"get_network_by_id: network_id={network_id} not found")
        return result

def search_subgraph(query_matrix: List[List[int]],
                    query_labels: List[str]) -> List[Dict]:
    """
    Sucht in DB nach Netzwerken, die query_matrix enthalten koennten.
    
    Nutzt C++-basierte Subgraph-Executor mit ProcessPoolExecutor für
    parallele nicht-blockierende Ausführung.
    """
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
        logger.info(f"search_subgraph: {len(candidates)} candidates for query (n={query_node_count}, e={query_edge_count})")

        matches = []
        for candidate in candidates:
            candidate_matrix = candidate['adjacency_matrix']  # Ist bereits Liste[Liste[int]]

            # Führe C++-Vergleich aus (non-blocking über ProcessPoolExecutor)
            result, error = compare_graphs_async(query_matrix, candidate_matrix)
            
            if error:
                logger.warning(f"search_subgraph: Comparison error for network {candidate['network_id']}: {error}")
                continue

            # Konvertiere C++-Result-Codes zu Match-Typen
            # KEEP_A (0): Query ist Subgraph von Candidate
            # KEEP_B (1): Candidate ist Subgraph von Query (Match!)
            # KEEP_BOTH (2): Keine Subgraph-Beziehung
            # IDENTICAL (3): Identische Graphen (Match!)

            if result in ['KEEP_B', 'IDENTICAL']:
                match_type = 'exact' if result == 'IDENTICAL' else 'subgraph'
                matches.append({
                    'network_id': candidate['network_id'],
                    'name': candidate['name'],
                    'network_type': candidate['network_type'],
                    'organism': candidate['organism'],
                    'node_labels': candidate['node_labels'],
                    'node_count': candidate['node_count'],
                    'edge_count': candidate['edge_count'],
                    'match_type': match_type,
                    'subgraph_result': result
                })

        logger.info(f"search_subgraph: Found {len(matches)} matches")
        return matches

def delete_network(network_id: int) -> bool:
    """Loescht Netzwerk aus DB (CASCADE loescht auch Matrix)"""
    logger.info(f"delete_network: network_id={network_id}")
    with get_db_connection() as conn:
        cursor = get_db_cursor(conn)
        cursor.execute("""
            DELETE FROM biological_networks WHERE network_id = %s
            RETURNING network_id
        """, (network_id,))
        deleted = cursor.fetchone() is not None
        if deleted:
            logger.info(f"delete_network: network_id={network_id} deleted successfully")
        else:
            logger.warning(f"delete_network: network_id={network_id} not found")
        return deleted
