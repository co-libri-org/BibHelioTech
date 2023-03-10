from web.bht_proxy import get_pipe_callback, pipe_paper_mocked


class TestBhtProxy:
    def test_get_pipe_callback(self):
        """
        GIVEN the get_pipe_callback method
        WHEN called with boolean
        THEN check it returns appropriate method
        """
        notest_callback = get_pipe_callback(test=False)
        test_callback = get_pipe_callback(test=True)
        assert test_callback.__name__ == "pipe_paper_mocked"
        assert notest_callback.__name__ == "pipe_paper"

    def test_pipepaper_mocked(self):
        """
        GIVEN the mocking pipepaper method
        WHEN called
        THEN check it slept
        """
        max_secs = 2
        slept = pipe_paper_mocked(min_secs=1, max_secs=max_secs)
        assert slept <= max_secs
