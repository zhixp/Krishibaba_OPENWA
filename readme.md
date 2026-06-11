# Krishibaba_OPENWA

We are locking the direction:

Phase 1: WhatsApp-first using OpenWA.
Goal: onboard 300–400 farmers, collect real voice clips, clean mandi/weather/query data, prove usage.
Phase 2: move to official WhatsApp or Android app once usage/data proves itself.
Long-term: Krishi Baba becomes the rural farmer intelligence/data layer.

The core correction from earlier: we are not jumping straight to Android. We start where farmers already are: WhatsApp.

Krishi Baba Master Plan
1. Product identity

Krishi Baba is not a generic chatbot.

It is:

A WhatsApp-first farming intelligence system for rural Indian farmers that understands voice, gives verified mandi/weather/farming answers, stores rural dialect data, and slowly builds a clean agri intelligence dataset.

The farmer-facing product:

“राम राम भैया, पूछो खेती का सवाल.”

The backend product:

structured rural intent data, mandi intelligence, crop issue data, voice/dialect dataset, partner-shop lead engine.

The old AgriBot plan already had the right instincts: brief answers, farmer onboarding, crop/location context, weather, mandi prices, and official-source farming advice. But it was too synchronous, too fragile, and too dependent on live scraping during chat.

2. Phase strategy
Phase 1: WhatsApp/OpenWA pilot

Target:

0 → 300/400 farmers

Stack:

OpenWA / WhatsApp Web transport
FastAPI backend
Gemini Flash / Lite
Supabase Postgres + Storage
Free VPS
Hindi text replies only
Audio input only, no audio output

Goal:

collect farmer questions
collect rural voice clips
test mandi lookup
test weather trust
test onboarding
test hallucination safety
test partner-shop monetization later
Phase 2: Harden or official WhatsApp

Move when:

OpenWA becomes unstable
message volume increases
number risk becomes serious
we need reliability
dealer/shop revenue starts

Official WhatsApp becomes easier once we know farmers actually use it.

Phase 3: Android app

Move only after:

300–400 real farmers
enough voice samples
clear top use cases
clean mandi/weather dataset
clear retention
some shop/dealer monetization signal

Android app should not be the experiment. It should be the upgrade.

3. Core architecture

Final architecture:

Farmer WhatsApp
   ↓
OpenWA Gateway
   ↓
Backend Channel API
   ↓
Message Normalizer
   ↓
Onboarding / User Memory
   ↓
Intent Router
   ↓
Safety Layer
   ↓
Data Services
      - Mandi DB
      - Weather APIs
      - Scheme DB
      - Farmer Profile
   ↓
Gemini Flash/Lite Formatter
   ↓
Hindi Text Reply
   ↓
Supabase Logs + Voice Dataset

Critical rule:

OpenWA is just a pipe. Backend is the brain.

The repo audit from the other agent made the same call: OpenWA should be a separate adapter, while FastAPI remains the unified intelligence engine for WhatsApp, voice, and future channels.

No farming logic inside OpenWA.

3A. Codex implementation discipline

Codex must not rewrite the repo blindly.

For every existing file, inspect first and mark one of:

keep
patch
replace

Rules:

Keep working weather, pincode, Agmarknet, prompt, and utility code where useful.
Patch files when the idea is correct but schema, auth, imports, or edge cases are broken.
Replace files only when the schema or core logic is fundamentally wrong for this WhatsApp-first architecture.
Do not delete useful prototype logic until the replacement exists and tests cover the behavior.
Do not move farming logic into OpenWA while cleaning up.

4. OpenWA role

OpenWA handles only:

incoming text
incoming audio
media download
forward message to backend
send backend reply
basic delivery/error logs

OpenWA does not handle:

Gemini prompts
mandi logic
weather logic
onboarding state
farmer memory
safety rules
dealer monetization

Reason:

When we move to official WhatsApp or Android, we replace only the transport.

Backend stays untouched.

5. AI model strategy

We use:

Gemini Lite = cheap extraction/classification
Gemini Flash = audio understanding + Hindi formatting
Gemini Pro = not used initially unless absolutely needed later

No audio replies.

We receive audio because it helps us build the dataset.

We reply in simple Hindi text.

Model usage
Mandi price query:
Lite extracts crop/mandi/location.
Backend fetches DB.
Flash formats reply.

Weather query:
Lite extracts location/time intent.
Backend checks weather APIs.
Flash formats simple Hindi report.

General farming question:
Flash gives brief answer, but only after safety classification.

Critical pesticide/fertilizer/disease:
Flash can classify and ask follow-up.
Backend safety gate decides whether direct answer is allowed.

Scheme question:
Backend retrieves verified source.
Flash explains in simple Hindi.

The AI must not invent facts.

The AI is a listener, router, translator, and formatter.

Truth comes from our data.

6. Hallucination control

This is non-negotiable.

Old problem:

AI gave confident answers without verified data.
AI sometimes forgot stored location.
Mandi intent triggered wrongly.
Weather/persona broke in some responses.

Final rule:

Every answer must be grounded, classified, and logged.

Risk levels
LOW:
Greeting, onboarding, casual explanation.

MEDIUM:
Mandi price, weather forecast, government scheme summary.

HIGH:
Crop disease, fertilizer advice, irrigation decision.

CRITICAL:
Pesticide dose, chemical recommendation, severe crop loss, financial eligibility, weather disaster warning.

BLOCKED:
Insufficient data, source unavailable, unsafe request.
Safety policy

For critical questions:

Never answer directly if key context is missing.
Ask follow-up first.
Never invent dosage.
Never recommend pesticide blindly.
Never claim scheme eligibility without source.
Never claim weather certainty beyond forecast confidence.

Example:

Farmer asks:

सोयाबीन में इल्ली लगी है कौन सी दवाई डालूं?

Bad answer:

ये दवाई डाल दो।

Correct answer:

भैया, सही दवाई बताने से पहले 4 बात बताओ:

1. फसल कितने दिन की है?
2. इल्ली पत्ती खा रही है या फली?
3. कितने खेत में दिख रही है?
4. फोटो भेज सकते हो क्या?

बिना ये देखे दवाई बताना ठीक नहीं रहेगा।

This builds trust.

7. Onboarding plan

We do not make onboarding feel like a government form.

We collect minimum info first.

First-time flow
राम राम भैया 🙏
मैं Krishi Baba हूँ।

आपका नाम क्या है?

Then:

कौन से गांव/पिनकोड से हो?

Then:

अभी कौन सी फसल लगी है?

Then:

आपकी आवाज़ और सवाल को सेवा सुधारने के लिए सुरक्षित रखा जा सकता है।
आपका नंबर किसी को नहीं दिया जाएगा।
अनुमति है तो “हाँ” लिखें।

Minimum required fields:

name
phone_hash
village/pincode
district
state
main_crop
language/dialect guess
consent status

Collect later when needed:

soil type
irrigation type
sowing date
land size
last pesticide
crop stage

Important:

If farmer already gave pincode/location, Krishi Baba must never ask it again unless data is unclear.

Old issue: bot asked for location even when farmer had already provided it. That must be killed.

8. Weather plan

Important correction:

Weather forecast and irrigation advice are separate intents.

Hard system spec:

Weather forecast intent:
- Give forecast only.
- Always show the next 3 days.
- Always show location used and forecast generated time.
- If rain appears after day 3 within the 8-10 day forecast window, add the exact date note.
- Do not give irrigation advice unless the farmer explicitly asks for irrigation.

Irrigation intent:
- Ask crop stage, soil moisture, last irrigation, and current field condition.
- Do not answer from weather alone.
- Use weather as one signal only after field condition is known.

If farmer asks:

बारिश कब होगी?
मौसम बताओ
अगले हफ्ते पानी है क्या?

We give forecast only.

No automatic “सिंचाई मत करो.”

Weather forecast answer

Always show:

location used
forecast generated time
next 3 days
rain chance
temperature
humidity if available
wind if available
source confidence
long-range note if rain appears after day 3

Example:

📍 मौसम रिपोर्ट: देवरी, सागर

अगले 3 दिन:

आज, 11 जून:
🌡 33°C
🌧 बारिश संभावना: 8%

12 जून:
🌡 34°C
🌧 बारिश संभावना: 12%

13 जून:
🌡 32°C
🌧 बारिश संभावना: 18%

अभी अगले 3 दिन तेज बारिश का संकेत नहीं है।

नोट:
8 दिन बाद, 19 जून को हल्की बारिश की संभावना दिख रही है।
लंबा forecast बदल सकता है, 2–3 दिन बाद फिर चेक कर लेना।
Irrigation answer

If farmer asks:

सिंचाई कर दूं?
पानी लगा दूं?

Then ask field condition:

सही सलाह के लिए 4 बात बताओ:

1. फसल कौन सी है?
2. कितने दिन की है?
3. मिट्टी अभी सूखी है या नमी है?
4. आखिरी सिंचाई कब की थी?

Only after that answer.

Weather APIs help, but they do not replace field condition.

9. Mandi price master plan

This is the data warehouse.

Mandi data is not just a feature.

It becomes our historical asset.

Old issue:

state/district/city/mandi mapping was breaking
mandi price failed when state/district/city were unclear
live scraping during chat caused latency and failure
crop/mandi synonyms caused wrong lookup

Final principle:

Never scrape during user chat. Scrape daily. Store clean. Serve instantly.

The SarpanchAI direction already identified database-first mandi lookup as superior to scrape-on-demand because it avoids lag and lets us calculate trends locally.

10. Mandi data source strategy

Primary:

Agmarknet / official mandi data

Secondary fallback:

Agriplus or other public sources

But every price row must have:

source
source_url/source_name
scraped_at
price_date
confidence
freshness_status

If source is not official, label it.

If data is stale, say stale.

No fake freshness.

11. Mandi ingestion pipeline

Daily job:

04:00 AM scrape starts
   ↓
fetch raw mandi data
   ↓
store raw source response
   ↓
parse rows
   ↓
normalize state/district/market/crop
   ↓
dedupe rows
   ↓
validate prices
   ↓
store clean daily rows
   ↓
update latest price view
   ↓
update historical trends
   ↓
log errors

Run again later if needed:

10:00 AM retry
04:00 PM retry for markets updated late

No user request waits for scraper.

User gets DB result instantly.

12. Mandi database design

We need two layers:

raw layer = never lose source data
clean layer = farmer-facing data
Raw tables
scrape_runs
raw_mandi_snapshots
raw_mandi_rows
scrape_errors

Purpose:

debugging
re-parsing later
auditing source changes
historical proof
Canonical tables
states
districts
mandis
commodities
commodity_aliases
mandi_aliases
location_aliases

Purpose:

solve spelling/synonym problems
avoid duplicate mandis
map local names to official names
Clean price tables
mandi_prices_daily
mandi_prices_latest
mandi_price_history
mandi_price_trends

Purpose:

fast answers
historical dataset
trend analysis
nearby mandi comparison
13. Mandi table fields
mandi_prices_daily
id
source
source_run_id
state
district
market_name_raw
market_id
commodity_name_raw
commodity_id
variety
grade
arrival_quantity
min_price
max_price
modal_price
price_unit
price_date
scraped_at
raw_row_hash
data_quality_status
confidence_score
created_at
mandi_prices_latest

This is a view/table for fast lookup.

market_id
commodity_id
latest_modal_price
latest_min_price
latest_max_price
latest_arrival_quantity
latest_price_date
freshness_status
source
confidence_score
updated_at
mandi_price_history

Append-only.

Never overwrite.

market_id
commodity_id
price_date
modal_price
min_price
max_price
arrival_quantity
source
confidence_score

This lets us build:

7-day trend
30-day trend
seasonal price movement
arrival vs price movement
best nearby mandi
price spread alerts
14. Mandi alias system

This fixes the exact state/district/city issue.

Farmers will say:

देवरी
देवरी मंडी
deori
deori mandi
देवरी सागर
sagar deori

Official source may say:

Deori
Deori(Sagar)
Deori F&V

So we need aliases.

mandi_aliases
id
alias_text
normalized_alias
market_id
state
district
confidence
created_by
created_at
commodity_aliases
soybean → सोयाबीन, soya, soyabean, soybean seed
paddy → धान, dhaan, rice paddy
wheat → गेहूं, gehu, gehun
gram → चना, chana
maize → मक्का, makka
onion → प्याज, pyaz
Resolve flow
farmer message
   ↓
extract crop/mandi/location
   ↓
normalize spelling
   ↓
check alias table
   ↓
if exact match found, use it
   ↓
if multiple matches, use farmer district/state
   ↓
if still unclear, ask one short clarification

Example:

भैया, देवरी नाम की 2 मंडी मिल रही हैं।
आप सागर वाली देवरी पूछ रहे हो?
15. Mandi ranking logic

Do not return random result.

Rank nearby mandis by:

exact mandi match
district match
state match
distance from farmer
data freshness
price confidence
arrival quantity
price spread
transport cost estimate

Formula concept:

final_score =
name_match_score
+ district_score
+ freshness_score
+ confidence_score
+ distance_score
+ arrival_score
- stale_penalty

The earlier repo audit also recommended ranking nearby mandis by distance, freshness, price spread, arrival trend, transport cost, and confidence.

16. Mandi response format

Farmer asks:

देवरी मंडी में सोयाबीन भाव?

Reply:

📊 सोयाबीन भाव — देवरी मंडी

💰 Modal भाव: ₹4,320 / क्विंटल
⬇️ Min: ₹4,100
⬆️ Max: ₹4,450

📅 तारीख: 11 जून
📍 जिला: सागर, MP
स्थिति: 🟢 ताज़ा डेटा

कल से: ₹40 ऊपर 📈

पास की मंडी:
1. रहली: ₹4,280
2. सागर: ₹4,350

भैया, मंडी जाने से पहले स्थानीय व्यापारी से एक बार confirm कर लेना।

If stale:

📊 सोयाबीन भाव — देवरी मंडी

आज का सरकारी डेटा नहीं मिला।
कल का भाव दिखा रहा हूँ:

💰 Modal: ₹4,280 / क्विंटल
📅 तारीख: 10 जून
स्थिति: 🟡 पुराना डेटा

मंडी जाने से पहले confirm कर लेना भैया।

If not found:

भैया, देवरी मंडी में आज सोयाबीन का भाव नहीं मिला।

पास की मंडियों में मिला:
1. सागर मंडी — ₹4,350
2. रहली मंडी — ₹4,280

आप इनमें से कौन सी मंडी देखना चाहते हो?
17. Mandi historical dataset

This is the money.

Over time we build:

crop-wise mandi trends
district-wise price movement
arrival vs price signal
supply shortage signal
best selling day patterns
nearby mandi arbitrage
seasonal price baseline

Farmer value:

आज बेचूँ या रुकूँ?
कौन सी मंडी बेहतर है?
किस मंडी में arrival ज्यादा है?
किस मंडी में भाव गिर रहा है?

B2B value:

district crop demand
farmer selling intent
price movement signals
supply pressure
local mandi intelligence

The bot becomes more than a price lookup.

It becomes rural market intelligence.

18. Voice data storage plan

Voice is the real moat.

But only if stored cleanly.

The other agent was right: rural voice notes only become valuable if we store raw audio, transcript, dialect guess, location/pincode/geohash, crop/pest intent, confidence, consent, anonymized version, response, and feedback. Without that, it is just a pile of files.

Store every audio as an event
voice_logs

Fields:

id
farmer_id
phone_hash
audio_storage_path
audio_duration_seconds
file_size_bytes
mime_type
language_guess
dialect_guess
transcript_raw
transcript_clean
intent
intent_confidence
crop
pest_or_disease
mandi
location_used
model_used
reply_id
consent_status
created_at
Store audio file in Supabase Storage

Do not store raw audio inside Postgres.

Postgres stores path + metadata.

Storage stores .ogg/.opus.

Consent

First interaction:

Krishi Baba आपकी आवाज़ और सवाल को सेवा सुधारने के लिए सुरक्षित रख सकता है।
आपका नंबर किसी को नहीं दिया जाएगा।
अनुमति है तो “हाँ” लिखें।

If no consent:

still serve farmer
do not use audio for training dataset
store only operational minimum
19. User memory plan

Do not store only “last 20 messages.”

Store structured farmer facts.

The earlier audit explicitly called this out: memory should store structured facts, not just recent chat history.

Farmer profile
farmer_id
phone_hash
name
village
pincode
district
state
main_crop
secondary_crops
soil_type
irrigation_type
sowing_date
crop_stage
land_size
preferred_language
dialect_guess
consent_audio_training
last_seen_at
Conversation memory
last_question
last_intent
pending_followup_fields
current_crop_context
current_location_context
last_mandi_requested
last_weather_requested

This fixes:

farmer already gave location but bot asks again
farmer gave crop earlier but bot forgets
mandi bot triggers during onboarding
weather uses wrong/default location
20. Intent router

Current keyword-only routing is too brittle for rural Hindi, Hinglish, misspellings, and voice transcription noise. The repo audit already identified that issue and recommended a hybrid router: rules first, lightweight LLM fallback.

Router flow
1. Check onboarding state first
2. Check hard keyword rules
3. Use Lite JSON classifier
4. Validate extracted entities
5. Assign risk level
6. Route to service

Important:

Onboarding has priority over mandi/weather intent.

Old bug:

farmer gave name + state
mandi bot triggered

Fix:

if onboarding_step != complete:
    do not trigger mandi/weather unless user clearly asks
Output JSON
intent
sub_intent
entities
risk_level
confidence
missing_fields
should_answer_directly
requires_data_source
21. Krishi Baba persona

The persona matters.

Old SarpanchAI felt like corporate ChatGPT.

The Krishi Baba tone was liked because it had warmth, humor, and local farmer energy. The file explicitly described the desired persona as a wise, culturally rooted farming assistant that gives brief, clear, actionable advice.

Persona rules:

warm rural Hindi
short answers first
uses भैया / राम राम naturally
slight humor, not clown behavior
never overdo emojis
never sound like government PDF
never fake certainty

Example:

राम राम भैया 🌾
सीधी बात बताता हूँ...

For weather, keep forecast clean, then small commentary only.

For critical topics, tone becomes serious.

No jokes in pesticide/disease emergency.

22. Government scheme data

Scheme questions are high-risk because wrong eligibility wastes farmer time.

Flow:

daily/weekly scrape official scheme pages
store raw page/PDF
extract clean scheme chunks
verify source/date
answer only from stored scheme data

Scheme tables:

scheme_sources
scheme_documents
scheme_chunks
scheme_eligibility_rules
scheme_updates

Reply format:

🏛 योजना: PM-Kisan

किसके लिए:
छोटे और सीमांत किसान...

जरूरी कागज:
Aadhaar, bank account, land record...

Source:
सरकारी पोर्टल से मिला डेटा

क्या आप आवेदन प्रक्रिया जानना चाहेंगे?

If source stale:

भैया, इस योजना का ताज़ा नियम मेरे पास confirm नहीं है।
गलत जानकारी देने से अच्छा है पहले official source check करना।
23. Partner shop monetization

Farmers do not pay.

Shops/dealers/FPOs/agri businesses pay.

But no hidden sponsored advice.

Hidden pesticide promotion will destroy trust.

Safe model

Neutral advice first.

Then clearly labelled offer:

पास में उपलब्ध offer:
Sharma Krishi Kendra पर DAP पर ₹40 discount चल रहा है।
Coupon: KISAN-4821
Coupon/parchi system

Flow:

farmer asks for input/product
   ↓
bot gives neutral advice
   ↓
shows nearby partner offer
   ↓
generates coupon
   ↓
shop validates coupon
   ↓
transaction logged
   ↓
monthly billing to shop

Tables:

partner_shops
shop_products
shop_offers
coupon_events
coupon_redemptions
lead_events
24. Admin dashboard

We need an internal command center.

Minimum admin metrics:

daily active farmers
new farmers
voice notes received
top crops
top mandis
top issues
failed intent classification
failed audio transcription
stale mandi data
scraper failures
weather API failures
critical questions blocked
AI cost estimate
storage used
coupon leads

Admin actions:

correct mandi alias
correct crop alias
approve scheme data
mark bad response
view unresolved questions
retry scraper
export voice dataset metadata

This is how the bot improves every day.

25. Observability

Every message gets a request ID.

Log:

message_received
channel
farmer_id
intent
entities
risk_level
model_used
tokens_estimated
latency_ms
data_source_used
reply_sent
error

Without logs, we are flying blind.

The repo audit also recommended structured logs, latency, AI cost, failed intent, and failed send tracking.

26. Supabase storage plan

Supabase stores:

farmer data
profiles
messages
voice metadata
mandi historical data
weather cache
scheme data
logs

Supabase Storage stores:

voice clips
raw scrape snapshots if needed
PDF scheme docs

Use Postgres for structured data.

Use Storage for files.

Do not dump huge blobs into DB.

Backup rule

Daily export:

mandi_prices_daily
voice_logs metadata
farmer_profiles
intent_events

Weekly export:

raw audio metadata
scheme data
scrape raw snapshots

Mandi history is an asset. Do not risk losing it.

27. Cost discipline

Current assumptions:

free VPS
Supabase free initially
Gemini Lite/Flash
OpenWA
no audio replies
no mass marketing
1–2 promo messages/month max

Main costs:

Gemini processing
Supabase storage later
domain/monitoring maybe

Cost stays low if we:

do not use Pro everywhere
do not generate audio replies
do not broadcast daily
do not use AI for simple DB lookups
cache weather/mandi
28. Testing plan

Before farmers touch it, test:

onboarding interruption
wrong pincode
farmer sends state instead of district
voice note with noisy background
mandi misspellings
crop synonyms
weather question
irrigation question
pesticide question
scheme question
stale mandi data
source unavailable
Gemini invalid JSON
OpenWA disconnect
Supabase timeout

Test cases:

“मेरा नाम रामलाल है”
“देवरी से हूँ”
“सोयाबीन लगा है”
“देवरी मंडी सोयाबीन भाव”
“बारिश कब होगी”
“सिंचाई कर दूं?”
“इल्ली लग गई क्या डालूं”
“पीएम किसान पैसा कब आएगा”
29. Execution order for Codex

This is the build sequence.

Step 1: Repo audit and cleanup

Codex should inspect current repo and list:

keep
merge
patch
replace
broken files
duplicate logic
security issues
schema mismatch

Codex should only replace a file when schema or core logic is broken.
Working weather, pincode, Agmarknet, prompt, and utility code must be preserved or patched where useful.

Known issues from previous audit:

uploaded_images inserted but table missing
broadcast schema mismatch
admin endpoints missing auth
legacy mobile app code removed from Phase 1 scope
keyword intent too brittle
JSON state storage unsafe

These came from the repo review in the uploaded agent chat.

Step 2: Fix existing runtime/schema bugs

Fix known broken behavior before adding new systems:

uploaded_images table missing
broadcast schema mismatch
admin endpoints missing auth
unsafe production defaults
duplicate chat paths
legacy mobile app code removed from Phase 1 scope

Step 3: Supabase schema

Create migrations for:

farmers
farmer_profiles
messages
conversation_sessions
voice_logs
intent_events
states
districts
mandis
commodities
mandi_aliases
commodity_aliases
scrape_runs
raw_mandi_rows
mandi_prices_daily
mandi_prices_latest
mandi_price_history
weather_cache
scheme_sources
scheme_chunks
partner_shops
coupon_events
system_logs
Step 4: Backend channel endpoint

Build:

POST /v1/channels/whatsapp/message

Responsibilities:

receive normalized text/audio events from OpenWA
resolve or create farmer
run onboarding first
store message and intent event
return Hindi text reply

Step 5: Onboarding engine

Build structured onboarding.

Must support:

skip
ni pata
voice answers
interrupted conversations
resume state
location reuse
Step 6: Mandi warehouse

Mandi becomes first-class before voice polish.

Daily scrape.

Raw + clean storage.

Alias resolver.

Latest view.

Historical table.

Trend engine.

Nearby mandi ranking.

No live scraping during chat.

Step 7: Weather forecast engine

Multi-source weather if possible.

3-day forecast always.

8-10 day exact date note if rain appears later.

No irrigation advice unless asked.

Irrigation intent must ask crop stage, soil moisture, last irrigation, and field condition.

Step 8: Intent router

Rules first, Gemini Lite fallback.

Strict JSON.

No free-form model routing.

Onboarding has priority over mandi/weather intent.

Step 9: Safety engine

Critical gates.

No pesticide/fertilizer/disease answer without context.

Weather forecast separated from irrigation advice.

Step 10: OpenWA gateway

Build:

whatsapp_gateway/

Responsibilities:

receive text
receive audio
download media
POST to backend
send text response
log delivery/error
no farming logic

Step 11: Voice pipeline

Store raw audio.

Gemini Flash for audio understanding.

Store transcript + intent + metadata.

Reply in Hindi text.

Step 12: Admin tools

Basic dashboard/endpoints.

Failed messages.

Scraper health.

Alias corrections.

Bad response review.

Step 13: Tests

Onboarding, intent, mandi, weather, safety, voice, storage, OpenWA failure.
