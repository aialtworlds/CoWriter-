import os
from anthropic import Anthropic


class ClaudeClient:
    def __init__(self):
        self.client = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
        self.model = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-5')

    def generate(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return ''.join(block.text for block in msg.content if getattr(block, 'type', None) == 'text')


claude = ClaudeClient()
