import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from . import crud
from .subgraph_executor import shutdown_executor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle Manager für FastAPI App.
    
    Startet ProcessPoolExecutor bei App-Start und fahrt ihn bei Shutdown herunter.
    """
    # Startup
    logger.info("Starting up Gen API with C++-based Subgraph Executor")
    yield
    # Shutdown
    logger.info("Shutting down Gen API and Subgraph Executor")
    shutdown_executor()


app = FastAPI(
    title="Gen - Biological Network Analysis API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NetworkCreate(BaseModel):
    name: str
    network_type: str
    organism: str
    description: Optional[str] = ""
    node_labels: List[str]
    adjacency_matrix: List[List[int]]

class NetworkSearch(BaseModel):
    node_labels: List[str]
    adjacency_matrix: List[List[int]]

@app.get("/")
async def root():
    """Serve frontend"""
    logger.info("GET / - Serving frontend")
    return FileResponse("src/frontend/index.html")

@app.get("/api/networks")
async def get_networks(limit: int = 33, random: bool = True):
    """
    Hole Netzwerke aus der Datenbank

    Args:
        limit: Maximale Anzahl (default: 33)
        random: Zufällige Auswahl (default: True)
    """
    logger.info(f"GET /api/networks limit={limit} random={random}")
    try:
        networks = crud.get_all_networks(limit=limit, random_sample=random)
        logger.info(f"GET /api/networks - Returned {len(networks)} networks")
        return {"success": True, "data": networks, "count": len(networks)}
    except Exception as e:
        logger.error(f"GET /api/networks - Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/networks/{network_id}")
async def get_network(network_id: int):
    logger.info(f"GET /api/networks/{network_id}")
    try:
        network = crud.get_network_by_id(network_id)
        if not network:
            logger.warning(f"GET /api/networks/{network_id} - Not found")
            raise HTTPException(status_code=404, detail="Network not found")
        logger.info(f"GET /api/networks/{network_id} - Found: {network['name']}")
        return {"success": True, "data": network}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET /api/networks/{network_id} - Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/networks")
async def create_network(network: NetworkCreate):
    logger.info(f"POST /api/networks - name={network.name} type={network.network_type} organism={network.organism}")
    try:
        result = crud.create_network(
            name=network.name,
            network_type=network.network_type,
            organism=network.organism,
            description=network.description or "",
            node_labels=network.node_labels,
            adjacency_matrix=network.adjacency_matrix
        )
        logger.info(f"POST /api/networks - Created network_id={result['network_id']}")
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"POST /api/networks - Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/networks/search")
async def search_networks(search: NetworkSearch):
    logger.info(f"POST /api/networks/search - nodes={len(search.node_labels)}")
    try:
        matches = crud.search_subgraph(
            query_matrix=search.adjacency_matrix,
            query_labels=search.node_labels
        )
        logger.info(f"POST /api/networks/search - Found {len(matches)} matches")
        return {"success": True, "data": matches}
    except Exception as e:
        logger.error(f"POST /api/networks/search - Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/networks/{network_id}")
async def delete_network(network_id: int):
    logger.info(f"DELETE /api/networks/{network_id}")
    try:
        deleted = crud.delete_network(network_id)
        if not deleted:
            logger.warning(f"DELETE /api/networks/{network_id} - Not found")
            raise HTTPException(status_code=404, detail="Network not found")
        logger.info(f"DELETE /api/networks/{network_id} - Deleted successfully")
        return {"success": True, "message": "Network deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DELETE /api/networks/{network_id} - Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    logger.info("GET /api/health")
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
