from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from . import crud

app = FastAPI(title="Gen - Biological Network Analysis API")

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
    return FileResponse("src/frontend/index.html")

@app.get("/api/networks")
async def get_networks(limit: int = 33, random: bool = True):
    """
    Hole Netzwerke aus der Datenbank
    
    Args:
        limit: Maximale Anzahl (default: 33)
        random: Zufällige Auswahl (default: True)
    """
    try:
        networks = crud.get_all_networks(limit=limit, random_sample=random)
        return {"success": True, "data": networks, "count": len(networks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/networks/{network_id}")
async def get_network(network_id: int):
    try:
        network = crud.get_network_by_id(network_id)
        if not network:
            raise HTTPException(status_code=404, detail="Network not found")
        return {"success": True, "data": network}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/networks")
async def create_network(network: NetworkCreate):
    try:
        result = crud.create_network(
            name=network.name,
            network_type=network.network_type,
            organism=network.organism,
            description=network.description or "",
            node_labels=network.node_labels,
            adjacency_matrix=network.adjacency_matrix
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/networks/search")
async def search_networks(search: NetworkSearch):
    try:
        matches = crud.search_subgraph(
            query_matrix=search.adjacency_matrix,
            query_labels=search.node_labels
        )
        return {"success": True, "data": matches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/networks/{network_id}")
async def delete_network(network_id: int):
    try:
        deleted = crud.delete_network(network_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Network not found")
        return {"success": True, "message": "Network deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)