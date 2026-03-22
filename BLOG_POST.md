# I Stopped Writing Regex to Parse Trading Cards

*How OpenAI's structured outputs replaced OCR pipelines with a single Pydantic model*

---

**12 min read | March 2026**

---

![Architecture diagram placeholder]

## The extraction problem no one talks about

I collect Pokemon cards with my daughter. Nothing serious—just a few packs here and there when we're at Target. But like any collector, I wanted to know what our cards were worth. So I did what any data person would do: I started building a pipeline.

The plan was simple. Take a photo of a card, OCR the text, parse out the relevant fields (name, set, card number, rarity), and search eBay for comps.

The reality was not simple.

Pokemon cards have wildly inconsistent layouts. Some have the set name at the bottom. Some have it on the side. Some use symbols instead of text. The font changes between sets. The card number format changes between eras. And that's before you get to Japanese cards, promo cards, or error cards.

I wrote regex. Then more regex. Then a state machine to handle the different layouts. Then I added special cases. Then I added more special cases. The codebase grew. The accuracy stayed around 70%.

Sound familiar?

This is the unspoken truth about unstructured data extraction: the hard part isn't the extraction. The hard part is maintaining the pipeline when the source format changes.

**That's my thesis on extraction: OCR + regex is a losing game. The format wins eventually.**

## The shift: Schema-first extraction

Then I discovered something that changed everything: OpenAI's structured outputs with Pydantic.

The idea is simple. Instead of:

1. Send image to vision model  
2. Get back freeform text  
3. Parse text with regex  
4. Handle edge cases  
5. Validate output  
6. Cry

You do:

1. Define a Pydantic model  
2. Pass it as `response_format`  
3. Get back a validated, typed object  

That's it. No JSON parsing. No code fences to strip. No malformed responses. The API guarantees the response conforms to your schema.

```python
class PokemonCard(BaseModel):
    pokemon_name: str = Field(description="Name of the Pokemon")
    hp: Optional[int] = Field(description="Hit points shown on the card")
    card_number: Optional[str] = Field(description="Card number (e.g. '150/165')")
    set_name: Optional[str] = Field(description="Set name (e.g. 'Scarlet & Violet 151')")
    rarity: Optional[str] = Field(description="Rarity (e.g. 'Holo Rare', 'Ultra Rare')")
    illustrator: Optional[str] = Field(description="Artist credited on the card")
    # ... more fields

completion = openai.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[...],
    response_format=PokemonCard,
)

card = completion.choices[0].message.parsed
```

The `card` variable is now a Pydantic object. Fully typed. IDE-autocomplete-friendly. Ready to use.

```python
print(card.pokemon_name)   # "Charizard"
print(card.hp)             # 150
print(card.illustrator)    # "Mitsuhiro Arita"
```

No regex. No parsing. No edge cases.

## The architecture

Here's what the flow looks like:

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌───────────┐
│  Card Image  │────▶│  OpenAI Vision   │────▶│  PokemonCard     │────▶│  eBay URL │
│  (URL/file)  │     │  + response_fmt  │     │  (Pydantic obj)  │     │  DataFrame│
└──────────────┘     └──────────────────┘     └──────────────────┘     └───────────┘
                      Schema-constrained        Typed, validated        Downstream
                      extraction                data object             applications
```

Three key design decisions make this work:

**1. The schema is the documentation**

Every field has a `description` parameter. These descriptions serve double duty: they document the schema for humans AND they guide the AI on what to extract.

```python
card_number: Optional[str] = Field(
    default=None, 
    description="Card number (e.g. '150/165')"
)
```

The example in the description helps the model understand the format you expect. It's prompt engineering embedded in your data model.

**2. Nullable fields handle uncertainty**

Not every card has every field. Old cards don't have illustrator credits. Promo cards don't have card numbers. The schema encodes this with `Optional[T]` rather than handling it downstream.

```python
edition: Optional[str] = Field(
    default=None, 
    description="Edition (e.g. '1st Edition', 'Unlimited')"
)
```

The model returns `None` when it can't confidently determine a value. No guessing. No hallucinating.

**3. Low temperature for factual extraction**

```python
temperature=0.1
```

You don't want creativity here. You want accuracy. Low temperature tells the model to stick to what it sees.

## From Pokemon to sports cards

The pattern generalizes immediately. Same architecture, different schema:

```python
class SportsCard(BaseModel):
    player_name: str = Field(description="Full name of the player")
    sport: Optional[str] = Field(description="Sport (Baseball, Football, Basketball, Hockey)")
    team: Optional[str] = Field(description="Team name")
    year: Optional[int] = Field(description="Year printed on the card")
    set_name: Optional[str] = Field(description="Set name (Topps Chrome, Panini Prizm, etc)")
    parallel: Optional[str] = Field(description="Parallel type (Refractor, Silver Prizm, Gold)")
    is_rookie_card: Optional[bool] = Field(description="True if marked as a rookie card")
    is_autograph: Optional[bool] = Field(description="True if the card contains an autograph")
    grade: Optional[str] = Field(description="Grade if visible (e.g. 'PSA 10', 'BGS 9.5')")
```

Same `extract_card()` function. Same `response_format` pattern. Different domain.

I built three notebooks:
- `pokemon_card_extractor.ipynb` → Pokemon cards + eBay search
- `pokemon_card_extractor_whatnot.ipynb` → Pokemon cards + Whatnot search
- `sports_card_extractor.ipynb` → Baseball/Football/Basketball + eBay search

All three follow the same pattern. Define schema. Extract. Search marketplace.

## Beyond trading cards

This approach works for any image-to-structured-data task:

**Invoices:**
```python
class Invoice(BaseModel):
    vendor: str = Field(description="Company name on the invoice")
    total: float = Field(description="Total amount due")
    line_items: List[LineItem] = Field(description="Individual charges")
    due_date: Optional[str] = Field(description="Payment due date in YYYY-MM-DD")
```

**Receipts:**
```python
class Receipt(BaseModel):
    store: str = Field(description="Store name")
    items: List[ReceiptItem] = Field(description="Purchased items")
    subtotal: float = Field(description="Subtotal before tax")
    tax: float = Field(description="Tax amount")
    total: float = Field(description="Total paid")
```

**Medical records, contracts, handwritten notes, business cards...** the pattern is always the same:

1. Define what you want
2. Let the model extract it
3. Get structured data back

## The economics

Each extraction costs about $0.01 with `gpt-4o-mini`. That's:
- ~8,500 tokens per call (image + schema + response)
- $0.15 per million input tokens
- $0.60 per million output tokens

At scale, you could extract 10,000 cards for ~$100.

Compare that to building and maintaining an OCR + regex pipeline. The human time alone makes structured outputs the obvious choice.

## BYOK: Bring Your Own Key

The whole project is designed for BYOK (Bring Your Own Key). No API keys hardcoded. No secrets in the repo. Just:

```bash
cp .env.example .env
# Add your OpenAI key
```

That's it. Anyone can clone the repo, add their key, and start extracting.

## What I learned

**The schema IS the product.** When you define a good schema, the extraction almost writes itself. Spend time on field descriptions and examples.

**Optional fields are your friend.** Real-world data is messy. Encode that messiness in your schema instead of handling it in post-processing.

**Vision models are surprisingly good at this.** I expected to need GPT-4o for accuracy. GPT-4o-mini handles 95%+ of cards correctly at 1/10th the cost.

**The marketplace URL is the killer feature.** Extraction alone is interesting. Extraction + search = useful. The `ebay_url` property turns a data object into an action.

## Try it yourself

**GitHub:** [github.com/dave-melillo/pokemonix](https://github.com/dave-melillo/pokemonix)

Clone it. Add your OpenAI key. Open a notebook. Extract a card.

```bash
git clone https://github.com/dave-melillo/pokemonix.git
cd pokemonix
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
jupyter notebook
```

The notebooks are self-contained. Run cell by cell. Watch the extraction happen. Click the eBay link. See what your cards are worth.

And if you extend it to a new domain—Magic cards, stamps, coins, whatever—let me know. The pattern generalizes. That's the whole point.

---

*Dave Melillo is a data engineering leader, author of Learn AI Data Engineering in a Month of Lunches, and a guy who now knows way too much about Charizard variants.*

*Follow me on [LinkedIn](https://linkedin.com/in/davemelillojr) for more on AI, data engineering, and the occasional hot take.*
