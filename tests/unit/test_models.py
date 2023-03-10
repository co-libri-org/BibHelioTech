from web.models import Paper


class TestModels:
    def test_paper(self):
        """
        GIVEN Paper model
        WHEN class is instantiated
        THEN verify existence
        """
        paper = Paper(title="title", pdf_path="path")
        assert paper.title == "title"
        assert paper.pdf_path == "path"
