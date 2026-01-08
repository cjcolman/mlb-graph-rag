from app.similarity import cosine_similarity, build_hitter_vector, top_k_similar

def test_cosine_similarity_identity_is_1():
    a = (1.0, 2.0, 3.0)
    assert abs(cosine_similarity(a, a) - 1.0) < 1e-9

def test_build_hitter_vector_rates():
    row = {
        "playerID": "p1",
        "name": "Player One",
        "year": 2022,
        "AB": 100,
        "HR": 10,
        "BB": 20,
        "SO": 30,
        "H": 40,
        "SB": 5,
    }
    v = build_hitter_vector(row)
    assert v.features[0] == 0.10  # HR/AB
    assert v.features[1] == 0.20  # BB/AB

def test_top_k_similar_excludes_self():
    t = build_hitter_vector({"playerID":"t","name":"T","year":2022,"AB":100,"HR":10,"BB":10,"SO":10,"H":30,"SB":0})
    c1 = build_hitter_vector({"playerID":"c1","name":"C1","year":2022,"AB":100,"HR":10,"BB":10,"SO":10,"H":30,"SB":0})
    c2 = build_hitter_vector({"playerID":"t","name":"T2","year":2022,"AB":100,"HR":0,"BB":0,"SO":0,"H":0,"SB":0})

    res = top_k_similar(t, [c1, c2], k=10)
    assert len(res) == 1
    assert res[0][0].playerID == "c1"
