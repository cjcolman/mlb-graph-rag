CREATE CONSTRAINT player_id IF NOT EXISTS
FOR (p:Player) REQUIRE p.playerID IS UNIQUE;

CREATE CONSTRAINT season_year IF NOT EXISTS
FOR (s:Season) REQUIRE s.yearID IS UNIQUE;

CREATE CONSTRAINT batting_key IF NOT EXISTS
FOR (b:BattingLine) REQUIRE (b.playerID, b.yearID) IS UNIQUE;

CREATE INDEX player_name IF NOT EXISTS
FOR (p:Player) ON (p.nameFull);
