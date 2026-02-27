# Talk Track: AI-Powered Data Extraction with Structured Outputs

## Presentation Script — Read This While Stepping Through the Notebook

---

## Opening / Context Setting

*Before opening the notebook:*

> Today I'm going to walk you through a pattern that I think represents a fundamental shift in how we approach data engineering. We're going to build a tool that takes an image of a Pokemon card, extracts structured data from it, and uses that data to search eBay for pricing.
>
> But the Pokemon card is just the vehicle. What I really want you to pay attention to is the **data engineering pattern** underneath — specifically, how we use AI as a **structured extraction layer** with deterministic, schema-enforced outputs. This is the same pattern you'd use for invoice processing, medical record extraction, receipt scanning, contract analysis — anywhere you need to go from unstructured input to clean, typed data.
>
> The key idea: **define your schema first, then let the AI conform to it** — not the other way around.

---

## Cell 1 — Setup & Install

*Run the pip install cell.*

> Nothing fancy here — we're installing four packages. But I want to call out the combination: **openai** for the AI extraction, **pydantic** for schema definition and validation, **pandas** for downstream analysis, and **python-dotenv** so we're not hardcoding API keys. This is a clean, minimal stack.

---

## Cell 2 — Imports & API Key

*Run the imports and API key cell.*

> A few things to notice in the imports. We're pulling in `BaseModel` and `Field` from Pydantic — these are going to do the heavy lifting for our schema. We're also importing `Optional` and `List` from typing because not every card will have every field, and we need to express that in our data model.
>
> The API key loads from a `.env` file. In a production pipeline, this would come from a secrets manager — Vault, AWS Secrets Manager, whatever your shop uses. The point is it's externalized, not embedded in the code.

---

## Cell 3 — The Data Model (PokemonCard)

*Run the PokemonCard class cell. Pause here — this is the most important cell in the notebook.*

> This is where I want to spend the most time, because **this is the cell that makes everything else work.** In traditional data engineering, when you're extracting data from unstructured sources, you typically have a pipeline that looks like: ingest raw data, write a bunch of regex or rules to parse it, hope it works, handle the exceptions when it doesn't.
>
> What we're doing here is fundamentally different. We're defining a **Pydantic BaseModel** — a typed Python class with validation built in — and we're going to hand this schema directly to the AI model and say: "fill this out."
>
> Let me walk through the fields. At the top, we have `pokemon_name` as a required `str`. Every other field is `Optional` — HP might not be visible, the illustrator might be cut off in the photo, the edition might not apply. That's a deliberate design choice. In data engineering, you always need to decide: what's required versus what's nullable? We're making that decision right here in the schema, not in some downstream cleaning step.
>
> Now look at the `Field` descriptors. Each field has a `description` parameter:
>
> ```python
> illustrator: Optional[str] = Field(
>     default=None,
>     description="Artist/illustrator credited on the card"
> )
> ```
>
> This is doing double duty. First, it's documentation — anyone reading this code knows exactly what each field means. Second, and this is the critical part — **these descriptions get sent to the OpenAI API as part of the JSON schema.** The AI model reads these descriptions to understand what data to extract and where to put it. So your documentation IS your extraction logic. That's a powerful idea.
>
> Compare this to the traditional approach. Without this, you'd be writing something like:
>
> ```python
> # Old way — fragile regex
> illustrator = re.search(r'Illus\.\s*(.+)', text)
> hp = re.search(r'HP\s*(\d+)', text)
> ```
>
> That regex breaks the moment the card layout changes, the OCR misreads a character, or the font is different. The AI approach is inherently more flexible because it understands the **semantics** of the card, not just the character patterns.
>
> Now let's look at the computed properties at the bottom. `ebay_search_query` is particularly interesting from a data engineering perspective — it's building a search string from the structured fields, not from raw text. That means we get a targeted query like `"Pokemon card Mewtwo 150/165 Scarlet & Violet 151 Holo Rare"` instead of dumping a paragraph of GPT prose into eBay's search bar. **Structured data enables better downstream logic.** That's the whole point.
>
> The `_repr_markdown_` method is a nice Jupyter touch — it renders the card as a formatted table right in the notebook. But notice it's using `model_dump()` under the hood, which is Pydantic's serialization. Everything flows from the schema.

---

## Cell 4 — The Extraction Function

*Run the extraction function cell. This is the second key cell.*

> Here's where the AI meets the schema. Let me draw your attention to the core API call:
>
> ```python
> completion = openai.beta.chat.completions.parse(
>     model="gpt-4o-mini",
>     messages=[...],
>     response_format=PokemonCard,
>     temperature=0.1,
> )
> ```
>
> Three things I want to highlight.
>
> **First: `response_format=PokemonCard`.** This is the game-changer. We're passing our Pydantic class directly as the response format. The OpenAI API takes this, converts it to a JSON schema, and **constrains the model's output to conform to that schema.** The model literally cannot return a response that doesn't match our data model. No malformed JSON, no missing fields, no surprise extra fields. This is what I mean by deterministic structured outputs.
>
> Think about what this replaces. In the old approach, you'd send a prompt that says "return JSON with these fields," get back raw text, strip markdown code fences if the model added them, try to parse the JSON, catch the exception if it's malformed, and then manually validate every field. That's five steps of fragile code replaced by one parameter.
>
> **Second: `temperature=0.1`.** We're keeping this very low because we want factual extraction, not creative interpretation. When you're doing data engineering with AI, temperature is your precision knob. For extraction tasks, keep it near zero. For generating descriptions or marketing copy, crank it up. Here we want the model to read what's on the card and report it accurately.
>
> **Third: the parsed response.** Look at how we access the result:
>
> ```python
> card = completion.choices[0].message.parsed
> ```
>
> That `.parsed` attribute gives us back a **fully validated PokemonCard instance.** Not a string, not a dict — an actual typed Python object. We can immediately do `card.illustrator`, `card.hp`, `card.ebay_url`. The AI extraction step and the validation step are the same step. That's a massive simplification of the pipeline.
>
> I also want to point out the refusal handling. If the model can't or won't parse the image, `.parsed` comes back as `None` and we check `.refusal` for the reason. In a production pipeline, this is where you'd route to a dead-letter queue or a manual review process.
>
> One more thing on the `build_image_content` helper — it handles both URLs and local file paths. For local files, it base64-encodes the image. This is important for batch processing where you might have a folder of card photos from a scanner or phone camera.

---

## Cell 5 — Preview the Card Image

*Run the image preview cell.*

> We're displaying the source image inline so we can visually verify the extraction results. This is just good practice — in any data pipeline, you want to be able to eyeball your inputs alongside your outputs. The `IPython.display.Image` widget handles this natively in Jupyter.

---

## Cell 6 — Run the Extraction

*Run the extraction cell. Wait for the result to render.*

> And there it is. Look at the table that just rendered. Every field we defined in our Pydantic model is populated — pokemon name, HP, card number, set, illustrator, year, attacks, all of it. And this came from an image. No OCR preprocessing, no regex, no hand-written parsing rules.
>
> Let me emphasize what just happened in data engineering terms. We went from an **unstructured image** to a **fully typed, validated data object** in a single API call. The schema we defined — the PokemonCard class — acted simultaneously as our extraction instructions, our validation rules, and our data contract. That's three traditional pipeline stages collapsed into one.
>
> Now, is the AI perfect every time? No. You'll occasionally get a wrong set name or a misread card number. But here's the thing — in the traditional regex/OCR approach, you get errors too, and they're harder to debug. With this approach, the errors are in the data, not in the parsing logic, which means they're easier to catch with standard data quality checks downstream.

---

## Cell 7 — Inspect the Data

*Run the field access cell.*

> This is where the Pydantic model pays off versus a raw dictionary. We're accessing `card.illustrator`, `card.hp`, `card.year` — these are typed attributes with autocomplete in any IDE. If you typo a field name, you get an AttributeError immediately, not a silent `None` from a dict `.get()` call three steps later.

---

## Cell 8 — model_dump()

*Run the model_dump cell.*

> `model_dump()` gives us back a plain dictionary — this is your on-ramp to everything else in the Python data ecosystem. You can dump this into a database, serialize it to JSON, send it to an API, feed it into a DataFrame. The Pydantic model is the canonical representation; everything else is a view of it.

---

## Cell 9 — JSON Serialization

*Run the model_dump_json cell.*

> Same data, JSON format. Notice the `indent=2` for readability. In production, you'd use `model_dump_json()` without indentation and write these to a JSON Lines file or push them into a message queue.

---

## Cell 10 — eBay Search

*Run the eBay search cell.*

> Now look at the search query that got constructed: it's clean, specific, and built from structured fields. This is the payoff of treating data as a first-class citizen. Instead of throwing raw GPT output at eBay's search bar — which would include stuff like "this appears to be a holographic Mewtwo card from the..." — we're constructing a precise query from typed fields.
>
> This is exactly what you'd do in any data-driven application. The AI does the extraction, the structured data drives the business logic. Clean separation of concerns.

---

## Cell 11 — Batch Processing

*Run the batch processing cell.*

> In the real world, you're not scanning one card — you're scanning a binder of 500. This loop processes a list of image URLs and collects the results. Notice the error handling: if one card fails, we log it and keep going. The `cards` list is fully typed as `list[PokemonCard]`, so downstream code knows exactly what it's working with.

---

## Cell 12 — DataFrame

*Run the DataFrame cell.*

> And here's where it all comes together. `model_dump()` on each card gives us a list of dicts, and pandas turns that into a DataFrame in one line. We're adding computed columns for the eBay query and URL. At this point, you could do anything — filter by rarity, sort by year, calculate average HP by set, export to CSV for a pricing spreadsheet.
>
> This is the pipeline: **image → AI extraction → Pydantic model → DataFrame → analysis.** Every step is typed, validated, and deterministic.

---

## Closing / Key Takeaways

*After the last cell:*

> Let me leave you with the key takeaways from a data engineering perspective.
>
> **One: Schema-first design.** Define your output structure before you write any extraction logic. The Pydantic model is your data contract — it tells the AI what to extract, validates the output, and documents the schema all in one place.
>
> **Two: `response_format` replaces brittle parsing.** Instead of regex, string splitting, JSON cleanup, and manual validation — you pass a Pydantic class and get back a validated object. This is more reliable than traditional approaches and dramatically less code.
>
> **Three: AI replaces rules, not engineers.** The AI handles the unstructured-to-structured conversion — the part that's hardest to write rules for. But the schema design, the downstream logic, the pipeline architecture, the quality checks — that's still data engineering. The AI is a tool in the pipeline, not a replacement for the pipeline.
>
> **Four: This pattern generalizes.** Swap out PokemonCard for Invoice, MedicalRecord, ContractClause, SupportTicket — the pattern is identical. Define a Pydantic model, pass it as `response_format`, get structured data back. That's the template.
>
> Thank you.
