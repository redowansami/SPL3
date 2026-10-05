"""A PyRIT PromptTarget that speaks the ATLAS-Scan JSON REST contract.

    POST <target_url>   body: render_request_body(template, <attack text>)
    reply: extract_response(response.json(), response_field)

PyRIT's built-in HTTPTarget wants a raw Burp-style request string; our targets are
described structurally (a JSON template + a response field), so we implement a small
target directly. It declares MULTI_TURN capability so RedTeamingAttack will drive a
multi-turn dialogue; the target endpoint itself can be stateless — PyRIT keeps the
conversation history and sends the newest attacker turn each time.
"""

import httpx
from pyrit.models import Message, MessagePiece, construct_response_from_request
from pyrit.prompt_target import PromptTarget
from pyrit.prompt_target.common.target_capabilities import TargetCapabilities
from pyrit.prompt_target.common.target_configuration import TargetConfiguration

from app.services.pyrit.runtime.request_body import extract_response, render_request_body

_MULTI_TURN_CONFIG = TargetConfiguration(
    capabilities=TargetCapabilities(supports_multi_turn=True)
)


class JsonRestTarget(PromptTarget):
    def __init__(
        self,
        *,
        target_url: str,
        request_template: dict,
        response_field: str,
        request_timeout: float,
    ) -> None:
        super().__init__(
            endpoint=target_url,
            model_name="atlas-scan-target",
            custom_configuration=_MULTI_TURN_CONFIG,
        )
        self._target_url = target_url
        self._request_template = request_template
        self._response_field = response_field
        self._request_timeout = request_timeout

    def _build_identifier(self):
        return self._create_identifier(params={"uri": self._target_url})

    async def _send_prompt_to_target_async(self, *, normalized_conversation: list[Message]) -> list[Message]:
        request_piece: MessagePiece = normalized_conversation[-1].message_pieces[0]
        prompt = request_piece.converted_value

        body = render_request_body(self._request_template, prompt)
        async with httpx.AsyncClient(timeout=self._request_timeout) as client:
            http_response = await client.post(
                self._target_url,
                json=body,
                headers={"Content-Type": "application/json"},
            )
            http_response.raise_for_status()
            reply_text = extract_response(http_response.json(), self._response_field)

        response_message = construct_response_from_request(
            request=request_piece, response_text_pieces=[reply_text]
        )
        return [response_message]
