# Pokemon Card Extractor & eBay Search

Extract structured data from Pokemon card images using OpenAI's vision API with **Pydantic structured outputs**, then search eBay for pricing.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## Why This Exists

Traditional card data extraction relies on OCR + regex — fragile pipelines that break when card layouts change, fonts differ, or image quality varies. This project replaces that entire approach with a single pattern:

1. **Define a schema** (Pydantic `BaseModel`)
2. **Pass it to the AI** via `response_format`
3. **Get back a validated, typed object** — no JSON parsing, no cleanup, no regex

The Pokemon card is the demo, but the pattern generalizes to invoices, receipts, medical records, contracts, or any unstructured-to-structured extraction task.

## How It Works

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌───────────┐
│  Card Image  │────▶│  OpenAI Vision   │────▶│  PokemonCard     │────▶│  eBay URL │
│  (URL/file)  │     │  + response_fmt  │     │  (Pydantic obj)  │     │  DataFrame│
└──────────────┘     └──────────────────┘     └──────────────────┘     └───────────┘
                      Schema-constrained        Typed, validated        Downstream
                      extraction                data object             applications
```

### Key Design Decisions

- **Schema-first**: The `PokemonCard` Pydantic model defines every field with types, defaults, and descriptions. The descriptions double as extraction instructions for the AI.
- **`response_format`**: OpenAI's structured outputs guarantee the response conforms to the schema. No malformed JSON, no missing fields, no code fence stripping.
- **Low temperature (0.1)**: Factual extraction, not creative interpretation.
- **Nullable fields**: Not every card has every field (edition, resistance, etc.). The schema encodes this with `Optional[T]` rather than handling it downstream.

## Quickstart

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/pokemon-card-extractor.git
cd pokemon-card-extractor
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Run the notebook

```bash
jupyter notebook pokemon_card_extractor.ipynb
```

### 4. Or use the CLI

```bash
python pokemon_card_extractor.py "https://m.media-amazon.com/images/I/71nbfl-JklS._AC_SY606_.jpg"
```

## Extracted Fields

| Field | Type | Description |
|:------|:-----|:------------|
| `pokemon_name` | `str` | Name of the Pokemon (required) |
| `hp` | `int?` | Hit points |
| `card_number` | `str?` | Card number (e.g. "150/165") |
| `set_name` | `str?` | Set name (e.g. "Scarlet & Violet 151") |
| `series` | `str?` | Series (e.g. "Scarlet & Violet") |
| `edition` | `str?` | Edition (e.g. "1st Edition", "Unlimited") |
| `rarity` | `str?` | Rarity (e.g. "Holo Rare", "Ultra Rare") |
| `illustrator` | `str?` | Artist/illustrator credit |
| `year` | `int?` | Copyright year |
| `card_type` | `str?` | Card type (e.g. "Basic", "Stage 1", "ex") |
| `weakness` | `str?` | Weakness type and modifier |
| `resistance` | `str?` | Resistance type and modifier |
| `retreat_cost` | `int?` | Number of energy symbols |
| `attacks` | `list[str]` | Attack names |
| `additional_notes` | `str?` | Promo info, special markings, errors |

## Example Output

```python
card = extract_card("https://m.media-amazon.com/images/I/71nbfl-JklS._AC_SY606_.jpg")

print(card.pokemon_name)      # "Mewtwo"
print(card.hp)                # 150
print(card.illustrator)       # "Mitsuhiro Arita"
print(card.ebay_search_query) # "Pokemon card Mewtwo 150/165 Scarlet & Violet 151 Holo Rare"
print(card.ebay_url)          # https://www.ebay.com/sch/i.html?_nkw=...
```

```python
# Batch process → DataFrame
cards = [extract_card(url) for url in urls]
df = pd.DataFrame([c.model_dump() for c in cards])
```

## The Pattern (Beyond Pokemon)

The extraction pattern is identical for any domain. Swap the model:

```python
class Invoice(BaseModel):
    vendor: str = Field(description="Company name on the invoice")
    total: float = Field(description="Total amount due")
    line_items: List[LineItem] = Field(description="Individual charges")
    due_date: Optional[str] = Field(description="Payment due date in YYYY-MM-DD")

completion = openai.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[...],
    response_format=Invoice,
)
invoice = completion.choices[0].message.parsed
```

Same for medical records, contracts, receipts, support tickets — define the schema, pass it as `response_format`, get structured data back.

## Project Structure

```
pokemon-card-extractor/
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
├── .env.example                     # Template for API key
├── .gitignore                       # Git ignore rules
├── pokemon_card_extractor.ipynb     # Jupyter notebook (interactive walkthrough)
├── pokemon_card_extractor.py        # CLI version (standalone script)
├── talk_track.md                    # Presentation script for stepping through the notebook
└── LICENSE                          # MIT License
```

## Presentation / Talk Track

The `talk_track.md` file contains a complete script you can read while stepping through the notebook cell by cell. It covers the data engineering concepts, the AI capabilities, and the key design decisions — useful for team demos, conference talks, or teaching.

## Requirements

- Python 3.10+
- OpenAI API key with access to `gpt-4o-mini` (or `gpt-4o`)
- ~$0.01 per card extraction (vision + structured output tokens)

## License

MIT
