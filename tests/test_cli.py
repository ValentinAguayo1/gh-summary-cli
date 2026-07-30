from gh_summary.cli import calculate_language_stats

def test_calculate_language_stats_success():
    mock_repos = [
        {'name': 'repo1', 'language': 'Python'},
        {'name': 'repo2', 'language': 'Python'},
        {'name': 'repo3', 'language': 'Java'},
    ]
    stats = calculate_language_stats(mock_repos)
    assert len(stats) == 2
    assert stats[0]['language'] == 'Python'
    assert stats[0]['count'] == 2

def test_calculate_language_stats_empty():
    mock_repos = [{'name': 'repo1', 'language': None}]
    stats = calculate_language_stats(mock_repos)
    assert stats == []
