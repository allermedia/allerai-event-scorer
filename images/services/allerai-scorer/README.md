## 2. Event Scorer

- Consumes enriched events from **ADP**.
- Fetches comparison events from **ADP / BigQuery** (with caching for efficiency).
- Computes **three feature types** for the event against comparison events:
  1. **Similarity** (via embeddings)
  2. **Classification overlap** (Google categories)
  3. **Entity matching** (person / tag overlap) -
- Calculates **per-site relevance scores** using weights domain specific weights defined in `domain_scoring.yaml`.
- Retrieves historical traffic data from ADP to:
  - Estimate potential traffic.
  - Place the event into a **traffic quartile**.
- Pushes a **scored payload** to pubsub for downstream consumption.

## Configuration

### Domain Scoring

Scoring behavior is configurable via `event_scorer/models/domain_scoring.yaml`, which defines per-domain weights for:

- Similarity
- Classification overlap
- Entity/tag matching

Features can be set as type "weighted" or "additive", with weighted being weighted against other weighted features.
Additive scores are added on top of the weighted features.

### Traffic Estimation

Uses historical traffic numbers from ADP to estimate pageview ranges.
