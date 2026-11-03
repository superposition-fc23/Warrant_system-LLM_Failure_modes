# Future plans

Inputs for the next version. Assumed figures are marked; the working is in report section 13.

## Human review cost

- **Measure a ruling, not just a label.** One blind review averaged about 4 minutes a record, median 2.75. Time real rulings, where the reason is shown, and split simple holds from hard ones.
- **Test the volume.** 0.2 to 1 money-action cases per customer a month is assumed. One log pull replaces it.
- **Price the mistakes.** Clawbacks, lost trust and retention, and manual overhead in account and relationship management are not in the table. Without them, review time alone does not justify the assumed account price.
- **Sample instead of reviewing everything.** Decide what share of cases needs a person, and what a second labeler adds. The first review had one self-declared selection error in 15.

## Review screen

- **Let a reviewer correct a mark without erasing it.** The first mark must stay, because the gate's answer is visible after marking and a silent change would no longer be blind. Today the correction can only go in the note field.

## From the human labels

- **Test one held state with a question.** A person used gather to mean "I need more context" on 2 records, and named the same need on a third, while the gate held. In code, gather only means a stale or missing source.
- **Name the date.** Invoice records carry a bare `date`, and the refund window depends on it. Say whether it is the invoice date or the paid date, in the source and in the prompt.
- **Get reviewers who did not build it.** 11 of 15 matched, but the reviewer is the author.

## Privacy

- **Catch unknown names.** Redaction relies on the roster, so a name outside it passes in free text.
- **Minimise contract text** before it reaches the provider, and settle provider retention before any real data.
