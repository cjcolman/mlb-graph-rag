import os
from dotenv import load_dotenv

load_dotenv()

import pandas as pd
from neo4j import GraphDatabase


LAHMAN_DIR = os.getenv("LAHMAN_DIR", "/app/../data/lahman")  # works in compose volume layout if you mount later

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    raise RuntimeError("Missing Neo4j environment variables")

def _load_people(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # People.csv usually has nameFirst, nameLast; create a convenient full name
    df["nameFull"] = (df["nameFirst"].fillna("") + " " + df["nameLast"].fillna("")).str.strip()
    # Keep only what we need for MVP
    keep = ["playerID", "nameFirst", "nameLast", "nameFull", "bats", "throws"]
    return df[keep].fillna("")

def _load_batting(path: str, year_min: int = 2015) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["yearID"] >= year_min].copy()  # keep it small initially
    # basic “line” stats
    keep = ["playerID", "yearID", "teamID", "lgID", "stint", "G", "AB", "R", "H", "HR", "BB", "SO", "SB", "CS"]
    for c in keep:
        if c not in df.columns:
            df[c] = None
    df = df[keep]
    df = df.fillna(0)
    # coerce ints safely
    for col in ["yearID", "stint", "G", "AB", "R", "H", "HR", "BB", "SO", "SB", "CS"]:
        df[col] = df[col].astype(int)
    return df

def ingest(people_csv: str, batting_csv: str, year_min: int = 2015) -> None:
    people = _load_people(people_csv)
    batting = _load_batting(batting_csv, year_min=year_min)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        # Players
        session.run(
            """
            UNWIND $rows AS row
            MERGE (p:Player {playerID: row.playerID})
            SET p.nameFirst = row.nameFirst,
                p.nameLast  = row.nameLast,
                p.nameFull  = row.nameFull,
                p.bats      = row.bats,
                p.throws    = row.throws
            """,
            rows=people.to_dict("records"),
        )

        # Seasons + BattingLine
        session.run(
            """
            UNWIND $rows AS row
            MERGE (s:Season {yearID: row.yearID})
            MERGE (b:BattingLine {playerID: row.playerID, yearID: row.yearID})
            SET b.teamID = row.teamID,
                b.lgID   = row.lgID,
                b.stint  = row.stint,
                b.G      = row.G,
                b.AB     = row.AB,
                b.R      = row.R,
                b.H      = row.H,
                b.HR     = row.HR,
                b.BB     = row.BB,
                b.SO     = row.SO,
                b.SB     = row.SB,
                b.CS     = row.CS
            WITH s, b, row
            MATCH (p:Player {playerID: row.playerID})
            MERGE (p)-[:HAS_BATTING_LINE]->(b)
            MERGE (b)-[:IN_SEASON]->(s)
            """,
            rows=batting.to_dict("records"),
        )

    driver.close()
    print("✅ Ingestion complete")

if __name__ == "__main__":
    people_csv = os.path.join(LAHMAN_DIR, "People.csv")
    batting_csv = os.path.join(LAHMAN_DIR, "Batting.csv")
    ingest(people_csv, batting_csv, year_min=int(os.getenv("YEAR_MIN", "2015")))
