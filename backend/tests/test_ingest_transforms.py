import pandas as pd
from app.ingest_lahman import _load_people, _load_batting

def test_load_people_builds_full_name(tmp_path):
    p = tmp_path / "People.csv"
    pd.DataFrame(
        [
            {"playerID": "a01", "nameFirst": "Aaron", "nameLast": "Judge", "bats": "R", "throws": "R"},
            {"playerID": "b02", "nameFirst": "Shohei", "nameLast": "Ohtani", "bats": "L", "throws": "R"},
        ]
    ).to_csv(p, index=False)

    df = _load_people(str(p))
    assert "nameFull" in df.columns
    assert df.loc[df["playerID"] == "a01", "nameFull"].iloc[0] == "Aaron Judge"

def test_load_batting_filters_year_min(tmp_path):
    p = tmp_path / "Batting.csv"
    pd.DataFrame(
        [
            {"playerID": "a01", "yearID": 2014, "G": 10, "AB": 20, "H": 5, "HR": 1, "BB": 2, "SO": 3, "R": 2, "SB": 0, "CS": 0, "teamID": "NYY", "lgID": "AL", "stint": 1},
            {"playerID": "a01", "yearID": 2016, "G": 50, "AB": 150, "H": 40, "HR": 10, "BB": 20, "SO": 60, "R": 30, "SB": 2, "CS": 1, "teamID": "NYY", "lgID": "AL", "stint": 1},
        ]
    ).to_csv(p, index=False)

    df = _load_batting(str(p), year_min=2015)
    assert df["yearID"].min() >= 2015
    assert len(df) == 1
