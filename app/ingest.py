import json
from dataclasses import asdict
from app.models import Record

GUIDE_URL = "https://pgsindia-ncof.gov.in/uploads/operational_manuals/165217720544Revised_PGS_India_Guidlines.pdf"
FAQ_URL = "https://pgsindia-ncof.gov.in/faqs"
G = "PGS-India Revised Guidelines, Edition 2 (2023)"
F = "PGS-India FAQ page"

# (topic, rule, applies_to, stage, source_doc, source_url)
RULES = [
    ("Local group minimum size",
     "A local group needs at least 5 members from the same or nearby villages with continuous territory. A group of about 7 to 10 is advisable so the group is not lost if a few members leave. If members fall below 5, the group becomes individual status and needs RC inspection or peer inspection by a nearby group, possibly at extra cost.",
     "local group", "formation", G + ", s4.1(a), s5.1", GUIDE_URL),

    ("Land holding limit per member (Edition 2)",
     "The land of one member must not exceed 50% of the total land under the group.",
     "farmer member", "formation", G + ", s4.1(e)", GUIDE_URL),

    ("Land holding limit per member (FAQ page)",
     "The FAQ page says one member's holding must not exceed one third of the group's total land. This differs from the 2023 Guidelines (50%), so always state which document the figure comes from.",
     "farmer member", "formation", F, FAQ_URL),

    ("Registration documents",
     "Each member needs a signed application form, farm history sheet and farmer pledge. Mobile and Aadhaar numbers are mandatory, bank details are optional. The group file also keeps the group agreement, farm maps with GPS coordinates, and one year of input and practice history for every member.",
     "farmer member", "registration", F + "; " + G + ", s4.2(c)", FAQ_URL),

    ("Farmer pledge",
     "Every member must sign the PGS organic pledge and the group agreement. The pledge is mandatory written proof of the member's commitment to organic practice.",
     "farmer member", "registration", G + ", s4.1(d), s4.2(a); " + F, GUIDE_URL),

    ("Endorsement of a new group",
     "Before registration the group's farms must be endorsed once by another registered PGS group. If none is nearby, the district agriculture officer or the Regional Council can verify the group. Groups formed under government schemes such as PKVY are endorsed by the district scheme officer.",
     "local group", "registration", G + ", s4.2(f), (i), (j)", GUIDE_URL),

    ("Start of conversion",
     "Conversion starts on the date the Regional Council grants registration. Only crops sown after registration approval qualify for PGS-Green, and using earlier seasons' data counts as a major non-compliance.",
     "local group", "conversion", F + "; " + G + ", s5.1 step 4", GUIDE_URL),

    ("PGS-Green versus PGS-Organic",
     "PGS-Organic is for farmers who completed the full conversion period with no major or serious non-compliance. PGS-Green is for farmers still in conversion or with one or more major non-compliances. PGS-Green is not a diluted organic standard, it is the same system during the conversion period.",
     "farmer member", "certification", G + ", s5.2; " + F, GUIDE_URL),

    ("PGS-Green time limit",
     "No member can hold PGS-Green status for more than 3 years for annual crops or 4 years for plantation or permanent crops. A member who still cannot qualify as PGS-Organic after that is sanctioned and excluded from the group.",
     "farmer member", "conversion", G + ", s5.2", GUIDE_URL),

    ("Peer appraisal team",
     "Each appraisal team needs at least 3 peer appraisers, and at least one must be literate and able to fill the forms. Reciprocal review is not allowed (A reviews B and B reviews A), and appraisers should be rotated.",
     "local group", "peer-appraisal", G + ", s5.1 step 3; " + F, GUIDE_URL),

    ("Peer appraisal frequency",
     "Every farm must be reviewed at least once in each season, and the farmer or a family member must be present. Edition 2 also says each farm should be appraised twice a year (s4.2(o)) and mentions a two-member team there, so check the Format-9 worksheet for the exact procedure.",
     "local group", "peer-appraisal", G + ", s5.1 step 3, s4.2(o); " + F, GUIDE_URL),

    ("Group meetings (Edition 2)",
     "Annual-crop groups hold 4 meetings a year (perennial-crop groups hold 2), and each member must attend at least 50% of them. The first training must happen within 6 months of registration.",
     "local group", "certification", G + ", s4.2(k), (l), s6.1.1", GUIDE_URL),

    ("Group meetings (FAQ page)",
     "The FAQ page says a group must meet at least 6 times a year and each member must attend at least 3 meetings. This differs from Edition 2 (4 meetings, 50% attendance), so state the document.",
     "local group", "certification", F, FAQ_URL),

    ("Large-area certification condition",
     "Large-area certification works village by village: one village is one group, and all farming members must follow PGS-India standards. The area needs no synthetic input or GMO use for at least 3 years, with an administrative ban on their sale. The Gram Panchayat must make every grower sign the pledge. Individual farmers and processors do not qualify.",
     "village", "certification", G + ", s4.5, s1.2.3", GUIDE_URL),

    ("Single defaulter consequence (large area)",
     "Under large-area certification, even one farmer's default can cancel the organic status of the entire village, and repeated defaults can cancel certification of the whole geographic block.",
     "village", "non-compliance", G + ", s4.5(m); " + F, GUIDE_URL),

    ("PGS standards and NPOP/NSOP",
     "PGS-India standards are the same as the National Standards for Organic Production (NSOP) under NPOP, and any NSOP amendment is treated as included. When a section is unclear, refer to NSOP. Food-processing additives and aids follow the NSOP approved list.",
     "farmer member", "standards", F + "; " + G + ", s5.4(l)", FAQ_URL),

    ("Prohibited substances",
     "Using chemical fertilizers, pesticides or hormones is a serious non-compliance: the member's status drops to zero, and the member is excluded or must re-register and complete the full conversion. Other major non-compliances can downgrade PGS-Organic to PGS-Green for one or two seasons.",
     "farmer member", "non-compliance", G + ", s5.1 step 4", GUIDE_URL),

    ("Off-farm inputs and seeds",
     "If a member uses or plans to use an off-farm input, the group must check its organic status and approve or prohibit it in a meeting, and use without approval is non-compliance. Hybrid and high-yielding seeds are allowed, genetically modified seeds are not, and untreated conventional seeds can be used only when organic seed is not available.",
     "farmer member", "production", G + ", s5.1 step 2(g); " + F, GUIDE_URL),

    ("Moving from NPOP or natural farming",
     "Operators moving from NPOP or the proposed natural-farming systems keep their certification status from the date the Regional Council accepts their application, provided they completed conversion as required by PGS-India standards and their scope certificate is valid on that date.",
     "farmer member", "certification", G + ", s5.8", GUIDE_URL),
]


def main():
    records = []
    bad = 0

    for row in RULES:
        try:
            topic, rule, applies_to, stage, source_doc, source_url = row
            if not rule.strip() or not source_url.startswith("http"):
                raise ValueError("bad row")
            records.append(asdict(Record(topic, rule, applies_to, stage,
                                         source_doc, source_url)))
        except ValueError:
            bad = bad + 1

    with open("data/records.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print("Saved", len(records), "records. Skipped", bad, "bad rows.")


if __name__ == "__main__":
    main()