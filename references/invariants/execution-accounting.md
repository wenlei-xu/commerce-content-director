# Execution accounting

Keep two counters separate:

- attempt_count: every submitted video Job attempt. Store it only in generation-jobs.json with run ID, script ID, attempt ID and payload digest.
- accepted_film_count: complete target-duration films that passed review, were attached to one final-film record and were freshly read as playable.

The script business counter is accepted_film_count. It changes exactly once after attachment verification. Stop if the stored value disagrees with qualifying final-film records.
