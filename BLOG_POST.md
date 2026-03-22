# Building a Card Value Lookup Tool with AI

*From Pokemon to Sports Cards: How I built an image-to-search pipeline using OpenAI's structured outputs*

---

**10 min read | March 2026**

---

## The Problem Every Collector Knows

I'm a sports card collector. Baseball, football, basketball—I've got boxes of cards going back years. And if you've ever collected cards, you know the pain: **looking up what your cards are worth is tedious.**

You pull a card from a pack. It's got some special shimmer. Maybe a serial number. Is this a $5 card or a $500 card? Time to find out.

So you open eBay. You type in the player name. You get 10,000 results. You add the year. Still 2,000 results. You try to remember what the parallel is called—is it a "refractor" or a "prizm" or a "wave"? You scroll through listings trying to match the visual pattern on your card to something in the search results.

Multiply that by 50 cards from a hobby box and you've lost your entire Saturday.

**I wanted to fix this.** Take a photo of a card, have AI extract all the relevant details, and generate a ready-to-click search URL.

I started with Pokemon cards. Not because I'm a huge Pokemon collector (though I do open packs with my daughter), but because **Pokemon cards are simpler from a data perspective**. One character per card. Clear set names. Consistent layouts. A good test case before tackling the messier world of sports cards.

---

## Part 1: The Pokemon Card Extractor

The core idea is simple:

1. Take an image of a card
2. Send it to an AI vision model
3. Get back structured data (not just text—actual typed fields)
4. Generate a marketplace search URL

The magic ingredient is **OpenAI's structured outputs with Pydantic**. Instead of getting freeform text that you have to parse, you define a schema and the API guarantees the response matches it.

### The Schema

```python
class PokemonCard(BaseModel):
    pokemon_name: str
    hp: Optional[int]
    card_number: Optional[str]
    set_name: Optional[str]
    rarity: Optional[str]
    edition: Optional[str]
    illustrator: Optional[str]
```

Each field has a description that guides the AI on what to extract. The `Optional` fields handle cases where information isn't visible on the card.

### The Extraction

```python
completion = openai.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [
            {"type": "text", "text": "Extract data from this card"},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]},
    ],
    response_format=PokemonCard,
)

card = completion.choices[0].message.parsed
```

That's it. `card` is now a fully typed Pydantic object. No JSON parsing. No regex. No cleanup.

### The Search URL

The schema includes computed properties that build search queries:

```python
@property
def ebay_search_query(self) -> str:
    tokens = []
    if self.set_name:
        tokens.append(self.set_name)
    tokens.append(self.pokemon_name)
    if self.card_number:
        tokens.append(f"#{self.card_number}")
    if self.rarity:
        tokens.append(self.rarity)
    return " ".join(tokens)

@property  
def ebay_url(self) -> str:
    return f"https://www.ebay.com/sch/i.html?_nkw={quote(self.ebay_search_query)}"
```

### The Result

Upload a Charizard card image, get back:

```
Pokemon: Charizard
Set: XY Evolutions  
Card #: 11/108
Rarity: Holo Rare

eBay Search: XY Evolutions Charizard #11/108 Holo Rare
```

Click the link, see comparable sales. Done in seconds instead of minutes.

**[Screenshot placeholder: eBay search results for extracted Pokemon card]**

---

## Part 2: Extending to Whatnot

Pokemon collectors don't just use eBay. **Whatnot** is huge for card sales—live auctions, direct listings, a dedicated collector community.

Extending to Whatnot was trivial. Same extraction logic, different URL format:

```python
@property
def whatnot_url(self) -> str:
    return f"https://www.whatnot.com/search?query={quote(self.whatnot_search_query)}&referringSource=typed"
```

That's it. One new property, one new notebook. Same card image, now searchable on two marketplaces.

**[Screenshot placeholder: Whatnot search results for same card]**

---

## Part 3: The Sports Card Challenge

Pokemon was the warmup. Sports cards are the real game.

Here's why sports cards are harder:

**1. More metadata.** Player name, team, position, year, manufacturer, product set, card number, serial number, parallel type, autograph, memorabilia, grading...

**2. Information is split.** The front has the player image and parallel appearance. The back has the year, card number, and fine print. You need both to fully identify a card.

**3. Visual patterns have specific names.** That checkered holographic pattern? It's called a "Checkerboard Refractor." That cracked ice look? "Cracked Ice Prizm." If you don't use the right term, your search won't find matches.

**4. Year is tricky.** A card showing "2024 Season Stats" is probably a 2025 card. The stats are from the previous season. The actual card year is in the copyright fine print.

I solved each of these.

### Solution 1: Front + Back Upload

The notebook now accepts two images—front and back of the card. Both get sent to the AI together, so it has full context.

```python
def extract_card(front_file=None, back_file=None):
    content_parts = []
    
    if front_file:
        content_parts.append({"type": "text", "text": "FRONT OF CARD:"})
        content_parts.append(encode_image(front_file))
    
    if back_file:
        content_parts.append({"type": "text", "text": "BACK OF CARD:"})
        content_parts.append(encode_image(back_file))
    
    # Send both to AI
    completion = openai.beta.chat.completions.parse(...)
```

The upload widget makes this easy:

```python
front_upload = widgets.FileUpload(description='Front of Card')
back_upload = widgets.FileUpload(description='Back of Card')
```

Upload both images, click Extract, get complete data.

### Solution 2: Year from Copyright Only

The prompt now has explicit instructions:

```
YEAR - **CRITICAL INSTRUCTION**:
⚠️ ONLY extract year from the COPYRIGHT LINE (e.g., "© 2025 Topps")
⚠️ DO NOT use years from statistics or season records
⚠️ Stats showing "2024 SEASON" means the CARD is from 2025
```

This fixed the Aaron Judge Topps Finest card that was incorrectly showing 2024 (the stats year) instead of 2025 (the copyright year).

### Solution 3: Visual Keywords + Known Parallels

The prompt now includes a comprehensive reference of parallel names:

```
TOPPS FINEST:
- Refractor (base shimmer)
- X-Fractor (X pattern)
- Checkerboard Refractor (checkered pattern)  ← Key for search!
- Oil Spill Refractor (rainbow swirls)
...

PANINI PRIZM:
- Cracked Ice (shattered ice look)
- Wave (flowing lines)
- Disco (sparkle dots)
...
```

And a new field captures searchable visual terms:

```python
visual_keywords: List[str]
# Example: ["Checkerboard", "Refractor", "Holographic"]
```

The eBay search now includes these:

**Before:** `2025 Topps Finest Aaron Judge #51`
**After:** `2025 Topps Finest Aaron Judge #51 Checkerboard Refractor`

That second search actually finds the specific parallel.

### The Sports Card Schema

```python
class SportsCard(BaseModel):
    # Core
    player_name: str
    team: Optional[str]
    sport: Optional[str]
    
    # Card details
    manufacturer: Optional[str]  # Topps, Panini, Upper Deck
    product_set: Optional[str]   # Chrome, Prizm, Finest
    year: Optional[int]          # From copyright only!
    card_number: Optional[str]
    
    # Rarity
    serial_number: Optional[str]  # e.g., "25/99"
    parallel_type: Optional[str]  # e.g., "Checkerboard Refractor"
    
    # Special features
    is_rookie_card: Optional[bool]
    is_autograph: Optional[bool]
    is_memorabilia: Optional[bool]
    
    # Visual (for search)
    visual_keywords: Optional[List[str]]
    
    # Grading
    grading_company: Optional[str]
    grade: Optional[str]
```

### Real Example: Aaron Judge Topps Finest

Front of card: Shows the checkerboard holographic pattern, player image.
Back of card: Shows "© 2025 THE TOPPS COMPANY", card #51.

**Extracted:**
```
Player: Aaron Judge
Year: 2025 (from copyright, not stats)
Set: Topps Finest
Card #: 51
Parallel: Checkerboard Refractor
Visual Keywords: ["Checkerboard", "Refractor", "Holographic"]

eBay Search: 2025 Topps Finest Aaron Judge #51 Checkerboard Refractor
```

That search query is specific enough to find comparable sales for this exact card variant.

**[Screenshot placeholder: Aaron Judge card extraction result + eBay search]**

---

## The Pattern Generalizes

The approach works for any image-to-structured-data task:

1. **Define a Pydantic schema** with descriptive fields
2. **Write a detailed system prompt** with domain knowledge
3. **Pass images + schema to OpenAI** with `response_format`
4. **Get typed, validated data back** with zero parsing

You could apply this to:
- Invoices and receipts
- Business cards
- Product photos
- Medical records
- ...anything with visual structure

---

## Try It Yourself

**GitHub:** [github.com/dave-melillo/pokemonix](https://github.com/dave-melillo/pokemonix)

Three notebooks:
- `pokemon_card_extractor.ipynb` → Pokemon + eBay
- `pokemon_card_extractor_whatnot.ipynb` → Pokemon + Whatnot
- `sports_card_extractor.ipynb` → Sports cards + eBay

Clone it, add your OpenAI key to `.env`, and start extracting.

```bash
git clone https://github.com/dave-melillo/pokemonix.git
cd pokemonix
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
jupyter notebook
```

The sports card notebook has file upload widgets—just drag and drop your card images. Works with photos from your phone.

---

## What I Learned

**Start simple, then extend.** Pokemon first, then Whatnot, then sports cards. Each step taught me something that improved the next.

**Domain knowledge matters.** Knowing that "Checkerboard Refractor" is a searchable term (not "checkered pattern") makes the difference between a useful search and a useless one.

**Both sides of the card matter.** For sports cards, the back has critical info (year, card number) that the front doesn't show.

**Copyright year ≠ stats year.** A card with "2024 Season Performance" is a 2025 card. This seems obvious in hindsight but the AI didn't know until I told it.

---

*Dave Melillo is a data engineering leader, sports card collector, and author of Learn AI Data Engineering in a Month of Lunches. He opens way too many hobby boxes.*

*[LinkedIn](https://linkedin.com/in/davemelillojr) | [GitHub](https://github.com/dave-melillo)*
