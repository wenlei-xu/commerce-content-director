# Workflow: 10-second clip production

Use this workflow when the user wants to build a reusable clip library or produce video material before assembling a complete film.

The production unit is one complete 10-second vertical video. Do not force the request into one action, one selling point or one shot. Give each 10-second clip one clear scene purpose, then let the generated footage contain a natural action arc. The user can later extract usable ranges from the finished 10-second mother clip.

1. Resolve the product, any explicitly bound subject, the scene intent and the clip's single broad purpose. A full 40-second script, full-film CTA, final voiceover and subtitle plan are not required.
2. Prepare one 9:16 first frame for the clip's entering state. The first frame may be generated as a clip asset and does not require the full-film A/B script-version package. Use the approved subject/scene references when applicable.
3. Submit one 10-second video-generation Job. Always upload or import the approved `product_anchor` and pass it as the first `input_asset_id`, even if the starting frame does not show the product. Pass the starting first frame and subject reference(s) after it.
4. Keep the video master clean: environmental sound is allowed, but do not burn in final subtitles, final voiceover or final CTA. Temporarily store the complete playable result in the draft clip library with the fields defined by [clip-library-contract.md](../domain/clip-library-contract.md). This is staging, not sedimentation.
5. Review the master for product fidelity, subject continuity, action completion, camera usability and generation artifacts. Mark the draft as 待筛选、入选 or 淘汰; do not treat generation success as creative acceptance.
6. When the user selects a usable portion, run the three blocking checks in
   the selected-clip admission gate in [clip-library-contract.md](../domain/clip-library-contract.md):
   complete action with a beginning and result, stable visuals without
   artifacts or deformation, and a clean playable video. Extract it as an
   independent clip only after those checks pass. If any check is uncertain,
   do not call it sedimentation: keep it out of the selected library and
   retain the mother clip in the draft library for review. Only a clip that
   passes all three checks is sedimented into the selected library. Store only
   the selected clip's own media and fields; do not require source linkage or
   extraction-time metadata.

The workflow stops after the draft or selected clip is written. Only an explicit request to assemble a final film enters [final-video.md](final-video.md), where the selected clip sequence, final voiceover and subtitles are resolved together.
