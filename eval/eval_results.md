# RAG evaluation results

15 questions (13 answerable, 2 that my documents cannot answer).

| Config | Chunk size | Top-k | Retrieval hit | Correct answers | Correct 'I don't know' | Overall |
|--------|-----------|-------|---------------|-----------------|------------------------|---------|
| A | 120 words | 3 | 12/13 | 12/13 | 2/2 | 14/15 |
| B (winner) | 60 words | 5 | 13/13 | 13/13 | 2/2 | 15/15 |

Average distance of the closest chunk (smaller = closer):

- Config A: answerable questions 0.367, unanswerable questions 0.527
- Config B: answerable questions 0.318, unanswerable questions 0.527

## Config A (120 words, top-3)

| id | question | answerable | retrieval hit | correct | distance | answer |
|----|----------|-----------|---------------|---------|----------|--------|
| 1 | How many farmers are needed to form a PGS-India local group? | True | yes | yes | 0.243 | A PGS-India local group must have at least 5 farmers, as stated in the PGS-India Revised Guidelines, Edition 2 (2023). |
| 2 | What is the difference between PGS-Green and PGS-Organic cer | True | yes | yes | 0.360 | PGS‑Organic certificates are issued to farmers who have finished the conversion period and have no major non‑compliance; they carry the PGS‑Organic logo. PGS‑Gr |
| 3 | Can one farmer's mistake cancel organic status for the whole | True | yes | yes | 0.336 | Yes, according to the PGS-India FAQ page, a single farmer’s default can cancel the organic status of the entire village. |
| 4 | Can one member of our group own most of the group's land? | True | yes | yes | 0.535 | No. According to the PGS‑India FAQ, a member’s land cannot be more than one‑third of the group’s total land [2]. The Revised Guidelines also say it should not e |
| 5 | Can I use chemical fertilizer on one plot and keep my other  | True | yes | yes | 0.562 | PGS-India guidelines say that you should not run parallel production of the same crop in organic and non‑organic plots, and they recommend using organic manures |
| 6 | How many group meetings must we hold each year and how many  | True | yes | yes | 0.385 | According to the PGS‑India Revised Guidelines, Edition 2 (2023), a group must hold 2 meetings a year if it grows perennial crops and 4 meetings a year if it gro |
| 7 | Can I export my PGS-certified produce as organic? | True | no | NO | 0.322 | I don't know. This is not in the PGS-India documents I have. |
| 8 | Is taking the farmer pledge compulsory? | True | yes | yes | 0.458 | Yes, taking the farmer pledge is compulsory in PGS-India. It is required for all members and serves as documented proof of commitment to organic farming. |
| 9 | Can an individual farmer get PGS certification without a gro | True | yes | yes | 0.213 | Yes, an individual farmer can be certified under the PGS‑India program, but this is only an interim arrangement. The farmer must try to bring other village memb |
| 10 | Can landless farmers with only cattle or poultry join a crop | True | yes | yes | 0.468 | According to the PGS‑India Standards and Revised Guidelines, landless livestock production is prohibited unless the farmer has a written cooperation agreement w |
| 11 | What forms must each member fill to join a PGS-India local g | True | yes | yes | 0.206 | To join a PGS‑India local group, each member must complete Annexure I (the application form), Annexure II (the farm history sheet) and the additional Annexure r |
| 12 | Is PGS-India a government approved certification system? | True | yes | yes | 0.204 | Yes, PGS-India is a government‑approved certification system. It is operated by the Department of Agriculture and Cooperation under the National Project on Orga |
| 13 | Why does a new local group need endorsement before registrat | True | yes | yes | 0.482 | A new local group needs endorsement before registration so the Regional Council can confirm that the group follows PGS-India standards and meets eligibility cri |
| 14 | Which shop in Pune pays the highest price for PGS-certified  | False | - | yes | 0.482 | I don't know. This is not in the PGS-India documents I have. |
| 15 | What is the market price of organic jaggery per kg in Kolhap | False | - | yes | 0.572 | I don't know. This is not in the PGS-India documents I have. |

## Config B (60 words, top-5)

| id | question | answerable | retrieval hit | correct | distance | answer |
|----|----------|-----------|---------------|---------|----------|--------|
| 1 | How many farmers are needed to form a PGS-India local group? | True | yes | yes | 0.194 | A PGS-India local group must have at least 5 farmers. The guidelines also suggest that a group of about 7-10 farmers is advisable. |
| 2 | What is the difference between PGS-Green and PGS-Organic cer | True | yes | yes | 0.250 | PGS-Organic is a full organic certification that lets a product use the PGS‑India organic logo and be sold as organic. PGS‑Green is for farms that are in the co |
| 3 | Can one farmer's mistake cancel organic status for the whole | True | yes | yes | 0.242 | Yes, according to the PGS-India Revised Guidelines (Edition 2, 2023) and the FAQ, even a single default by one farmer can lead to cancellation of organic status |
| 4 | Can one member of our group own most of the group's land? | True | yes | yes | 0.471 | No. A member cannot own most of the group’s land. The PGS-India Revised Guidelines (Edition 2, 2023) say a single member’s holding must not exceed 50% of the gr |
| 5 | Can I use chemical fertilizer on one plot and keep my other  | True | yes | yes | 0.528 | According to the PGS-India Revised Guidelines, chemical fertilizers are prohibited in organic farming, so a plot that receives them cannot be certified organic. |
| 6 | How many group meetings must we hold each year and how many  | True | yes | yes | 0.272 | According to the PGS‑India Revised Guidelines (Edition 2, 2023) a group should hold at least 2–4 meetings a year (2 for perennial crop groups and 4 for annual c |
| 7 | Can I export my PGS-certified produce as organic? | True | yes | yes | 0.318 | No, PGS-certified produce cannot be exported as organic; they can be exported as conventional according to the PGS-India FAQ page. |
| 8 | Is taking the farmer pledge compulsory? | True | yes | yes | 0.406 | Yes, taking the farmer pledge is mandatory in PGS-India. It is a documented proof of a farmer’s commitment to the organic production system, as stated in the PG |
| 9 | Can an individual farmer get PGS certification without a gro | True | yes | yes | 0.251 | Yes, an individual farmer can obtain PGS certification without a group. According to the PGS-India Revised Guidelines, Edition 2 (2023), an individual farmer wh |
| 10 | Can landless farmers with only cattle or poultry join a crop | True | yes | yes | 0.445 | No, under PGS‑India guidelines a farmer who has no organically managed land cannot produce livestock products. To join a crop production group they must have or |
| 11 | What forms must each member fill to join a PGS-India local g | True | yes | yes | 0.226 | Each member must fill an Application form, a Farm history sheet, and a Farmers pledge, and provide their mobile number and Aadhar number for the application. |
| 12 | Is PGS-India a government approved certification system? | True | yes | yes | 0.176 | Yes, PGS-India is a government approved certification system run by the Department of Agriculture and Cooperation under the National Project on Organic Farming. |
| 13 | Why does a new local group need endorsement before registrat | True | yes | yes | 0.352 | A new local group needs endorsement before registration because PGS‑India requires it to ensure the group is genuine and trustworthy. The endorsement comes from |
| 14 | Which shop in Pune pays the highest price for PGS-certified  | False | - | yes | 0.490 | I don't know. This is not in the PGS-India documents I have. |
| 15 | What is the market price of organic jaggery per kg in Kolhap | False | - | yes | 0.565 | I don't know. This is not in the PGS-India documents I have. |
