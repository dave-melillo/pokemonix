"""
Pokemon Card Image Extractor & eBay Search Tool

Extracts structured card data from an image using OpenAI's structured outputs
(response_format + Pydantic), then constructs targeted eBay search URLs.

Usage:
    python pokemon_card_extractor.py <image_url_or_path>
    python pokemon_card_extractor.py https://m.media-amazon.com/images/I/71nbfl-JklS._AC_SY606_.jpg
"""

import os
import sys
import base64
import webbrowser
from urllib.parse import quote
from typing import Optional, List

import openai
from dotenv import load_dotenv
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Load environment
# ---------------------------------------------------------------------------
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# ---------------------------------------------------------------------------
# Data model – first-class citizen for every card we extract
# ---------------------------------------------------------------------------
class PokemonCard(BaseModel):
    """Structured representation of a Pokemon card extracted from an image."""

    pokemon_name: str = Field(description="Name of the Pokemon (e.g. 'Mewtwo', 'Charizard ex')")
    hp: Optional[int] = Field(default=None, description="Hit points shown on the card")
    card_number: Optional[str] = Field(default=None, description="Card number (e.g. '150/165')")
    set_name: Optional[str] = Field(default=None, description="Set name (e.g. 'Scarlet & Violet 151')")
    series: Optional[str] = Field(default=None, description="Series (e.g. 'Scarlet & Violet', 'Sword & Shield')")
    edition: Optional[str] = Field(default=None, description="Edition (e.g. '1st Edition', 'Unlimited')")
    rarity: Optional[str] = Field(default=None, description="Rarity (e.g. 'Holo Rare', 'Ultra Rare', 'Common')")
    illustrator: Optional[str] = Field(default=None, description="Artist/illustrator credited on the card")
    year: Optional[int] = Field(default=None, description="Copyright year printed on the card")
    card_type: Optional[str] = Field(default=None, description="Card type (e.g. 'Basic', 'Stage 1', 'V', 'VMAX', 'ex')")
    weakness: Optional[str] = Field(default=None, description="Weakness type and modifier")
    resistance: Optional[str] = Field(default=None, description="Resistance type and modifier")
    retreat_cost: Optional[int] = Field(default=None, description="Number of energy symbols for retreat cost")
    attacks: List[str] = Field(default_factory=list, description="List of attack names on the card")
    additional_notes: Optional[str] = Field(default=None, description="Promo info, special markings, errors, etc.")

    @property
    def display_name(self) -> str:
        parts = [self.pokemon_name]
        if self.card_number:
            parts.append(f"({self.card_number})")
        if self.set_name:
            parts.append(f"- {self.set_name}")
        if self.rarity:
            parts.append(f"- {self.rarity}")
        return " ".join(parts)

    @property
    def ebay_search_query(self) -> str:
        """Build a focused eBay search string from the structured fields."""
        tokens = ["Pokemon card", self.pokemon_name]
        if self.card_number:
            tokens.append(self.card_number)
        if self.set_name:
            tokens.append(self.set_name)
        if self.edition:
            tokens.append(self.edition)
        if self.rarity:
            tokens.append(self.rarity)
        return " ".join(tokens)

    @property
    def ebay_url(self) -> str:
        return f"https://www.ebay.com/sch/i.html?_nkw={quote(self.ebay_search_query)}"

    def summary(self) -> str:
        lines = []
        for field_name, value in self.model_dump().items():
            if value is not None and value != []:
                label = field_name.replace("_", " ").title()
                if isinstance(value, list):
                    value = ", ".join(value)
                lines.append(f"  {label:<16}: {value}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Extraction logic
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are an expert Pokemon card analyst. Given an image of a Pokemon card, "
    "extract every piece of structured information you can identify from the card. "
    "Be precise with card numbers, set names, and illustrator credits. "
    "Use null for any field you cannot confidently determine from the image."
)


def build_image_content(image_source: str) -> dict:
    """Build the image content block for either a URL or a local file path."""
    if image_source.startswith(("http://", "https://")):
        return {
            "type": "image_url",
            "image_url": {"url": image_source},
        }
    else:
        with open(image_source, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(image_source)[1].lower().lstrip(".")
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "jpeg")
        return {
            "type": "image_url",
            "image_url": {"url": f"data:image/{mime};base64,{b64}"},
        }


def extract_card(image_source: str) -> PokemonCard:
    """
    Send an image to OpenAI's vision model and return a validated PokemonCard.

    Uses structured outputs (response_format) so the API returns a
    Pydantic-validated object directly — no JSON parsing required.
    """
    completion = openai.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all structured data from this Pokemon card image."},
                    build_image_content(image_source),
                ],
            },
        ],
        response_format=PokemonCard,
        temperature=0.1,
    )

    card = completion.choices[0].message.parsed

    if card is None:
        refusal = completion.choices[0].message.refusal
        raise ValueError(f"Extraction failed: {refusal or 'No structured output returned'}")

    return card


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python pokemon_card_extractor.py <image_url_or_path>")
        sys.exit(1)

    image_source = sys.argv[1]
    print(f"Extracting card data from: {image_source}\n")

    card = extract_card(image_source)

    print("=" * 50)
    print("EXTRACTED CARD DATA")
    print("=" * 50)
    print(card.summary())
    print()
    print(f"Raw JSON:\n{card.model_dump_json(indent=2)}")
    print()
    print(f"eBay search query: {card.ebay_search_query}")
    print(f"eBay URL: {card.ebay_url}")
    print()

    open_browser = input("Open eBay search in browser? [y/N] ").strip().lower()
    if open_browser == "y":
        webbrowser.open(card.ebay_url)


if __name__ == "__main__":
    main()
