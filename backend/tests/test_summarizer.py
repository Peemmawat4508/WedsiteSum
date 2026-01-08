import pytest
from unittest.mock import patch, MagicMock
from summarizer import simple_summarize, create_chunks, summarize_text

def test_simple_summarize_basic():
    text = "This is sentence one. This is sentence two. " * 5
    summary = simple_summarize(text, max_length=50)
    assert len(summary) <= 55  # allow some buffer for exact break
    assert summary.endswith('.')

def test_simple_summarize_short_text():
    text = "Short text."
    summary = simple_summarize(text)
    assert summary == "Short text."

def test_create_chunks_basic():
    text = "1234567890" * 100  # 1000 chars
    chunks = create_chunks(text, chunk_size=100, overlap=0)
    assert len(chunks) == 10
    assert len(chunks[0]) == 100

def test_create_chunks_overlap():
    text = "1234567890" * 20 
    # chunk_size=50, overlap=10
    chunks = create_chunks(text, chunk_size=50, overlap=10)
    # Just check if we get chunks and they seem reasonable
    assert len(chunks) > 0
    # Check overlap (crudely)
    if len(chunks) > 1:
        assert chunks[0][-10:] == chunks[1][:10]

@patch("summarizer.get_openai_client")
def test_summarize_text_mocked(mock_get_client):
    # Mock the client and response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Mocked summary"
    mock_client.chat.completions.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    text = "Some long text " * 100
    summary = summarize_text(text)
    
    assert summary == "Mocked summary"
    mock_client.chat.completions.create.assert_called_once()

@patch("summarizer.get_openai_client")
def test_summarize_text_fallback(mock_get_client):
    # Mock no client available
    mock_get_client.return_value = None
    
    text = "Sentence one. Sentence two."
    summary = summarize_text(text)
    
    # Should fall back to simple_summarize
    assert summary == text
