import pytest
from agents.provider import MockProvider

@pytest.mark.asyncio
async def test_mock_provider_matching():
    provider = MockProvider(
        response_map={
            "generate code": "Here is the code output",
            "say hello": "Hello world!"
        },
        default_response="Default response"
    )
    
    # Matching prompts
    res1 = await provider.generate([{"role": "user", "content": "Can you generate code for me?"}], model="test")
    assert res1 == "Here is the code output"
    
    res2 = await provider.generate([{"role": "user", "content": "Please say hello."}], model="test")
    assert res2 == "Hello world!"
    
    # Fallback default prompt
    res3 = await provider.generate([{"role": "user", "content": "What is the capital of France?"}], model="test")
    assert res3 == "Default response"
    
    # History check
    assert len(provider.history) == 3
    assert provider.history[0][1] == "test"
