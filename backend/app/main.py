from fastapi import FastAPI, Query
from .db import get_driver
from .similarity import build_hitter_vector, top_k_similar, explain_similarity, FEATURE_NAMES


app = FastAPI(title="MLB Graph RAG (Lahman MVP)")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/player/search")
def player_search(q: str = Query(min_length=2)):
    cypher = """
    MATCH (p:Player)
    WHERE toLower(p.nameFull) CONTAINS toLower($q)
    RETURN p.playerID AS playerID, p.nameFull AS name
    ORDER BY name
    LIMIT 20
    """
    driver = get_driver()
    with driver.session() as s:
        rows = s.run(cypher, q=q).data()
    return {"results": rows}

@app.get("/player/{player_id}/season/{year}")
def player_season(player_id: str, year: int):
    cypher = """
    MATCH (p:Player {playerID: $player_id})-[:HAS_BATTING_LINE]->(b:BattingLine {yearID: $year})
    RETURN p.playerID AS playerID, p.nameFull AS name, b.yearID AS year,
           b.G AS G, b.AB AS AB, b.H AS H, b.HR AS HR, b.BB AS BB, b.SO AS SO, b.R AS R
    """
    driver = get_driver()
    with driver.session() as s:
        row = s.run(cypher, player_id=player_id, year=year).single()
    return row.data() if row else {"error": "Not found"}

@app.get("/player/{player_id}/season/{year}/similar")
def similar_hitters(player_id: str, year: int, k: int = 10, min_ab: int = 200):
    driver = get_driver()

    cypher_target = """
    MATCH (p:Player {playerID: $player_id})-[:HAS_BATTING_LINE]->(b:BattingLine {yearID: $year})
    RETURN p.playerID AS playerID, p.nameFull AS name, b.yearID AS year,
           b.AB AS AB, b.HR AS HR, b.BB AS BB, b.SO AS SO, b.H AS H, b.SB AS SB
    """

    cypher_candidates = """
    MATCH (p:Player)-[:HAS_BATTING_LINE]->(b:BattingLine {yearID: $year})
    WHERE b.AB >= $min_ab
    RETURN p.playerID AS playerID, p.nameFull AS name, b.yearID AS year,
           b.AB AS AB, b.HR AS HR, b.BB AS BB, b.SO AS SO, b.H AS H, b.SB AS SB
    """

    with driver.session() as s:
        target_row = s.run(cypher_target, player_id=player_id, year=year).single()
        if not target_row:
            return {"error": "Target player/year not found"}

        target_vec = build_hitter_vector(target_row.data())

        candidate_rows = s.run(cypher_candidates, year=year, min_ab=min_ab).data()
        candidates = [build_hitter_vector(r) for r in candidate_rows]

    top = top_k_similar(target_vec, candidates, k=k)

    return {
    "target": {
        "playerID": target_vec.playerID,
        "name": target_vec.name,
        "year": target_vec.year,
        "AB": target_vec.AB,
        "features": dict(zip(FEATURE_NAMES, target_vec.features)),
    },
    "feature_definition": FEATURE_NAMES,
    "results": [
        {
            "playerID": v.playerID,
            "name": v.name,
            "year": v.year,
            "AB": v.AB,
            "similarity": round(score, 6),
            "explanation": explain_similarity(target_vec, v, top_similar=2, top_different=2),
            "features": dict(zip(FEATURE_NAMES, v.features)),
        }
        for v, score in top
    ],
    "params": {"k": k, "min_ab": min_ab},
}
