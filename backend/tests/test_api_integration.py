import pytest
from neo4j import GraphDatabase

pytestmark = pytest.mark.integration

def _docker_available() -> bool:
    try:
        from testcontainers.core.docker_client import DockerClient
        DockerClient().client.ping()
        return True
    except Exception:
        return False

if not _docker_available():
    pytest.skip("Docker not available - skipping integration tests", allow_module_level=True)

from testcontainers.neo4j import Neo4jContainer

@pytest.fixture(scope="session")
def neo4j():
    # Neo4jContainer expects NEO4J_AUTH in "user/password" form
    with Neo4jContainer("neo4j:5") as c:
        c.with_env("NEO4J_AUTH", "neo4j/password")
        yield c

def test_can_write_and_read_player(neo4j):
    uri = neo4j.get_connection_url()
    driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))

    with driver.session() as s:
        s.run("CREATE CONSTRAINT player_id IF NOT EXISTS FOR (p:Player) REQUIRE p.playerID IS UNIQUE")
        s.run("MERGE (p:Player {playerID:'test01'}) SET p.nameFull='Test Player'")
        r = s.run("MATCH (p:Player {playerID:'test01'}) RETURN p.nameFull AS name").single()
        assert r["name"] == "Test Player"

    driver.close()
