# LinkedIn Post Draft

---

**Hook + Content:**

I've written a lot of regex in my career.

Parsing invoices. Extracting values from PDFs. Scraping structured data from messy HTML.

Then I started collecting Pokemon cards with my daughter. Naturally, I wanted to know what they were worth. So I built a pipeline: OCR → regex → eBay search.

It was terrible. Different layouts. Different fonts. Different card formats. The regex grew. The accuracy didn't.

Then I discovered OpenAI's structured outputs with Pydantic.

Now the entire "pipeline" is:

1. Define a schema (Pydantic model)
2. Pass it to the API as response_format
3. Get back a typed, validated object

No parsing. No regex. No edge cases.

The same pattern works for:
🎴 Pokemon cards
⚾ Sports cards (baseball, football, basketball)
📄 Invoices, receipts, business cards...

I open-sourced the whole thing. Clone it, add your OpenAI key, run a notebook.

**That's my thesis on extraction:** the hard part isn't the extraction—it's maintaining the pipeline when the format changes. Structured outputs kill that problem.

🔗 Blog: [link]
🔗 GitHub: github.com/dave-melillo/pokemonix

---

**Suggested hashtags:**

#AI #MachineLearning #DataEngineering #OpenAI #Python #Pydantic #LLM #TradingCards

---

**Image suggestion:** 

Screenshot of the notebook showing extraction results, or a before/after comparing regex code vs. Pydantic schema.

---

**Call to action:**

What's the messiest unstructured data you've had to parse? Would love to hear war stories in the comments.
