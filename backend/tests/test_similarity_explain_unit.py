from app.similarity import build_hitter_vector, explain_similarity

def test_explain_similarity_has_similarities_and_differences():
    t = build_hitter_vector({"playerID":"t","name":"T","year":2024,"AB":100,"HR":10,"BB":10,"SO":25,"H":30,"SB":10})
    c = build_hitter_vector({"playerID":"c","name":"C","year":2024,"AB":100,"HR":3,"BB":9,"SO":22,"H":24,"SB":9})

    exp = explain_similarity(t, c, top_similar=2, top_different=2)
    assert "similarities" in exp and len(exp["similarities"]) == 2
    assert "differences" in exp and len(exp["differences"]) == 2
    assert "summary" in exp and len(exp["summary"]) > 0