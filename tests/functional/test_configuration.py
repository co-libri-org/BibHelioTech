from web.models import Paper


def test_papers_list_for_test(paperslist_for_tests):
    """
    GIVEN the fixture
    WHEN is called
    THEN check integrity
    """
    assert len(paperslist_for_tests) == 6
    papers_in_db = Paper.query.all()
    assert len(papers_in_db) == 6
