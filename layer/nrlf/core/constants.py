from enum import Enum


class Source(Enum):
    NRLF = "NRLF"
    LEGACY = "NRL"


VALID_SOURCES = frozenset(item.value for item in Source.__members__.values())
EMPTY_VALUES = ("", None, [], {})
REQUIRED_CREATE_FIELDS = [
    "custodian",
    "id",
    "type",
    "status",
    "subject",
    "category",
    "author",
]
JSON_TYPES = {dict, list}
NHS_NUMBER_INDEX = "idx_nhs_number_by_id"
ID_SEPARATOR = "-"
CUSTODIAN_SEPARATOR = "."
TYPE_SEPARATOR = "|"
KEY_SEPARATOR = "#"
ODS_SYSTEM = "https://fhir.nhs.uk/Id/ods-organization-code"
NHS_NUMBER_SYSTEM_URL = "https://fhir.nhs.uk/Id/nhs-number"
SNOMED_SYSTEM_URL = "http://snomed.info/sct"
RELATES_TO_REPLACES = "replaces"
ALLOWED_RELATES_TO_CODES = {
    RELATES_TO_REPLACES,
    "transforms",
    "signs",
    "appends",
    "incorporates",
    "summarizes",
}
CLIENT_RP_DETAILS = "nhsd-client-rp-details"
CONNECTION_METADATA = "nhsd-connection-metadata"
PERMISSION_AUDIT_DATES_FROM_PAYLOAD = "audit-dates-from-payload"
PERMISSION_SUPERSEDE_IGNORE_DELETE_FAIL = "supersede-ignore-delete-fail"
PERMISSION_ALLOW_ALL_POINTER_TYPES = "allow-all-pointer-types"


NHSD_REQUEST_ID_HEADER = "NHSD-Request-Id"
NHSD_CORRELATION_ID_HEADER = "NHSD-Correlation-Id"
X_REQUEST_ID_HEADER = "X-Request-Id"
X_CORRELATION_ID_HEADER = "X-Correlation-Id"


PRODUCER_URL_PATH = "/producer/FHIR/R4/DocumentReference"


class PointerTypes(Enum):
    MENTAL_HEALTH_PLAN = "http://snomed.info/sct|736253002"
    EMERGENCY_HEALTHCARE_PLAN = "http://snomed.info/sct|887701000000100"
    EOL_COORDINATION_SUMMARY = "http://snomed.info/sct|861421000000109"
    RESPECT_FORM = "http://snomed.info/sct|1382601000000107"
    NEWS2_CHART = "http://snomed.info/sct|1363501000000100"
    CONTINGENCY_PLAN = "http://snomed.info/sct|325691000000100"
    EOL_CARE_PLAN = "http://snomed.info/sct|736373009"
    LLOYD_GEORGE_FOLDER = "http://snomed.info/sct|16521000000101"
    ADVANCE_CARE_PLAN = "http://snomed.info/sct|736366004"
    TREATMENT_ESCALATION_PLAN = "http://snomed.info/sct|735324008"
    SUMMARY_RECORD = "http://snomed.info/sct|824321000000109"
    PERSONALISED_CARE_AND_SUPPORT_PLAN = "http://snomed.info/sct|2181441000000107"
    MRA_UPPER_LIMB_ARTERY = "https://nicip.nhs.uk|MAULR"
    MRI_AXILLA_BOTH = "https://nicip.nhs.uk|MAXIB"
    APPOINTMENT = "http://snomed.info/sct|749001000000101"
    SHARED_CARE_RECORD = "http://snomed.info/sct|887181000000106"

    @staticmethod
    def list():
        return list(map(lambda type: type.value, PointerTypes))

    def coding_system(self):
        return self.value.split(TYPE_SEPARATOR)[0]

    def coding_value(self):
        return self.value.split(TYPE_SEPARATOR)[1]


class Categories(Enum):
    CARE_PLAN = "http://snomed.info/sct|734163000"
    OBSERVATIONS = "http://snomed.info/sct|1102421000000108"
    CLINICAL_NOTE = "http://snomed.info/sct|823651000000106"
    DIAGNOSTIC_STUDIES_REPORT = "http://snomed.info/sct|721981007"
    DIAGNOSTIC_PROCEDURE = "http://snomed.info/sct|103693007"
    RECORD_ARTIFACT = "http://snomed.info/sct|419891008"
    RECORD_HEADINGS = "http://snomed.info/sct|716931000000107"

    @staticmethod
    def list():
        return list(map(lambda category: category.value, Categories))

    def coding_system(self):
        return self.value.split(TYPE_SEPARATOR)[0]

    def coding_value(self):
        return self.value.split(TYPE_SEPARATOR)[1]


CATEGORY_ATTRIBUTES = {
    Categories.CARE_PLAN.value: {
        "display": "Care plan",
    },
    Categories.OBSERVATIONS.value: {
        "display": "Observations",
    },
    Categories.CLINICAL_NOTE.value: {
        "display": "Clinical note",
    },
    Categories.DIAGNOSTIC_STUDIES_REPORT.value: {
        "display": "Diagnostic studies report",
    },
    Categories.DIAGNOSTIC_PROCEDURE.value: {
        "display": "Diagnostic procedure",
    },
    Categories.RECORD_ARTIFACT.value: {"display": "Record artifact"},
    Categories.RECORD_HEADINGS.value: {"display": "Record headings"},
}

TYPE_ATTRIBUTES = {
    PointerTypes.MENTAL_HEALTH_PLAN.value: {
        "display": "Mental health crisis plan",
    },
    PointerTypes.EMERGENCY_HEALTHCARE_PLAN.value: {
        "display": "Emergency health care plan",
    },
    PointerTypes.EOL_COORDINATION_SUMMARY.value: {
        "display": "End of life care coordination summary",
    },
    PointerTypes.RESPECT_FORM.value: {
        "display": "ReSPECT (Recommended Summary Plan for Emergency Care and Treatment) form",
    },
    PointerTypes.NEWS2_CHART.value: {
        "display": "Royal College of Physicians NEWS2 (National Early Warning Score 2) chart",
    },
    PointerTypes.CONTINGENCY_PLAN.value: {
        "display": "Contingency plan",
    },
    PointerTypes.EOL_CARE_PLAN.value: {
        "display": "End of life care plan",
    },
    PointerTypes.LLOYD_GEORGE_FOLDER.value: {
        "display": "Lloyd George record folder",
    },
    PointerTypes.ADVANCE_CARE_PLAN.value: {
        "display": "Advance care plan",
    },
    PointerTypes.TREATMENT_ESCALATION_PLAN.value: {
        "display": "Treatment escalation plan",
    },
    PointerTypes.SUMMARY_RECORD.value: {
        "display": "Summary record",
    },
    PointerTypes.PERSONALISED_CARE_AND_SUPPORT_PLAN.value: {
        "display": "Personalised Care and Support Plan",
    },
    PointerTypes.MRA_UPPER_LIMB_ARTERY.value: {
        "display": "MRA Upper Limb Rt",
    },
    PointerTypes.MRI_AXILLA_BOTH.value: {
        "display": "MRI Axilla Both",
    },
    PointerTypes.APPOINTMENT.value: {
        "display": "Appointment",
    },
    PointerTypes.SHARED_CARE_RECORD.value: {"display": "Clinical summary"},
}

TYPE_CATEGORIES = {
    #
    # Care plans
    PointerTypes.MENTAL_HEALTH_PLAN.value: Categories.CARE_PLAN.value,
    PointerTypes.EMERGENCY_HEALTHCARE_PLAN.value: Categories.CARE_PLAN.value,
    PointerTypes.EOL_COORDINATION_SUMMARY.value: Categories.CARE_PLAN.value,
    PointerTypes.RESPECT_FORM.value: Categories.CARE_PLAN.value,
    PointerTypes.CONTINGENCY_PLAN.value: Categories.CARE_PLAN.value,
    PointerTypes.EOL_CARE_PLAN.value: Categories.CARE_PLAN.value,
    PointerTypes.LLOYD_GEORGE_FOLDER.value: Categories.CARE_PLAN.value,
    PointerTypes.ADVANCE_CARE_PLAN.value: Categories.CARE_PLAN.value,
    PointerTypes.TREATMENT_ESCALATION_PLAN.value: Categories.CARE_PLAN.value,
    PointerTypes.PERSONALISED_CARE_AND_SUPPORT_PLAN.value: Categories.CARE_PLAN.value,
    #
    # Observations
    PointerTypes.NEWS2_CHART.value: Categories.OBSERVATIONS.value,
    #
    # Clinical notes
    PointerTypes.SUMMARY_RECORD.value: Categories.CLINICAL_NOTE.value,
    #
    # Imaging
    PointerTypes.MRA_UPPER_LIMB_ARTERY.value: Categories.DIAGNOSTIC_STUDIES_REPORT.value,
    PointerTypes.MRI_AXILLA_BOTH.value: Categories.DIAGNOSTIC_PROCEDURE.value,
    #
    # Bookings and Referrals
    PointerTypes.APPOINTMENT.value: Categories.RECORD_ARTIFACT.value,
    #
    # Shared Care Records
    PointerTypes.SHARED_CARE_RECORD.value: Categories.RECORD_HEADINGS.value,
}

PRACTICE_SETTING_VALUE_SET_URL = (
    "https://fhir.nhs.uk/England/ValueSet/England-PracticeSetting"
)
SNOMED_PRACTICE_SETTINGS = {
    "2471000175109": "Employee health service",
    "828331000000102": "Homeopathy service",
    "893041000000108": "Transient ischaemic attack service",
    "893391000000101": "Adult cystic fibrosis service",
    "828811000000104": "Child psychiatry service",
    "741073001": "Neonatal intensive care service",
    "3801000175108": "Pediatric pulmonology service",
    "893521000000108": "Respiratory physiology service",
    "892801000000107": "Audiological medicine service",
    "892571000000101": "Medical oncology service",
    "893421000000107": "Tropical medicine service",
    "1060971000000108": "General practice service",
    "907271000000106": "Genetics laboratory service",
    "224891009": "Healthcare services",
    "893771000000104": "Paediatric respiratory medicine service",
    "893591000000106": "Paediatric metabolic disease service",
    "892771000000109": "Cardiothoracic transplantation service",
    "92151000000102": "Mental health crisis resolution team",
    "893141000000109": "Nephrology service",
    "829981000000108": "Community child health service",
    "733459009": "Cardiac rehabilitation service",
    "893971000000101": "Paediatric burns care service",
    "931851000000100": "Oral pathology service",
    "3771000175106": "Pediatric gastroenterology service",
    "893621000000109": "Paediatric ear nose and throat service",
    "828281000000107": "Eating disorders service",
    "893121000000102": "Spinal surgery service",
    "892751000000100": "Clinical immunology and allergy service",
    "893601000000100": "Paediatric medical oncology service",
    "3751000175100": "Pediatric emergency medical service",
    "893951000000105": "Paediatric cardiology service",
    "931831000000107": "Oral medicine service",
    "829961000000104": "Out of hours service",
    "911381000000108": "Telehealthcare service",
    "828181000000101": "Community sexual and reproductive health",
    "2451000175103": "Perinatology service",
    "893851000000100": "Paediatric neurosurgery service",
    "109201000000109": "Substance misuse team",
    "893671000000108": "Paediatric urology service",
    "932271000000104": "Oral and maxillofacial surgery service",
    "444933003": "Home hospice service",
    "444913002": "Diabetes mellitus service",
    "892601000000108": "Intermediate care service",
    "893801000000101": "Paediatric ophthalmology service",
    "911231000000103": "Remote health monitoring service",
    "893091000000103": "Infectious diseases service",
    "893221000000106": "Specialist rehabilitation service",
    "828381000000103": "Well woman service",
    "907301000000109": "National Health Service 111 service",
    "828511000000102": "National Health Service 24",
    "893701000000107": "Paediatric thoracic surgery service",
    "828861000000102": "Programmed pulmonary rehabilitation service",
    "931781000000102": "Acute medicine service",
    "827641000000101": "Anticoagulant service",
    "893201000000102": "Sport and exercise medicine service",
    "278032008": "Preventive service",
    "892731000000107": "Dental medicine service",
    "893451000000102": "Respite care service",
    "2351000175106": "Sports medicine service",
    "893271000000105": "Medical virology service",
    "708168004": "Mental health service",
    "708169007": "Respiratory therapy service",
    "708171007": "Vascular ultrasound service",
    "708170008": "Nursing service",
    "708173005": "Obstetric ultrasound service",
    "708172000": "Cardiac ultrasound service",
    "708175003": "Diagnostic imaging service",
    "708178001": "Cytogenetics service",
    "708174004": "Interventional radiology service",
    "708179009": "Molecular pathology service",
    "708183009": "Anatomic pathology service",
    "708182004": "Histology service",
    "708180007": "Dermatopathology service",
    "708187005": "Surgical pathology service",
    "708185002": "Virology service",
    "708184003": "Clinical pathology service",
    "708188000": "Serology service",
    "708194008": "Blood bank service",
    "708196005": "Hematology service",
    "708191000": "Toxicology service",
    "708190004": "Immunology service",
    "708193002": "Coagulation service",
    "89301000000108": "Community mental health team",
    "893301000000108": "Local specialist rehabilitation service",
    "893651000000104": "Paediatric clinical immunology and allergy service",
    "893171000000103": "Clinical neurophysiology service",
    "711332004": "Allergy service",
    "893151000000107": "Nuclear medicine service",
    "894001000000107": "Paediatric audiological medicine service",
    "892781000000106": "Burns care service",
    "3781000175109": "Pediatric infectious disease service",
    "893631000000106": "Paediatric diabetic medicine service",
    "827621000000108": "Addiction service",
    "893531000000105": "Psychiatric intensive care service",
    "893881000000106": "Paediatric maxillofacial surgery service",
    "893051000000106": "Clinical allergy service",
    "893351000000109": "Complex specialised rehabilitation service",
    "893001000000105": "Clinical genetics service",
    "908981000000101": "Remote triage and advice service",
    "931811000000104": "Histopathology service",
    "1079481000000104": "Perinatal psychiatry service",
    "893251000000101": "Mental health recovery and rehabilitation service",
    "3531000175102": "Geriatric service",
    "736622005": "Aboriginal health service",
    "983641000000106": "Fracture liaison service",
    "893711000000109": "Neonatal critical care service",
    "828521000000108": "National Health Service Direct",
    "892761000000102": "Clinical haematology service",
    "901221000000102": "Perinatal mental health service",
    "706902008": "Mycology service",
    "706901001": "Bacteriology service",
    "706903003": "Mycobacteriology service",
    "706900000": "Parasitology service",
    "893131000000100": "Genitourinary medicine service",
    "413294000": "Community health services",
    "413299005": "Early years services",
    "828291000000109": "Dispensing optometry service",
    "413331009": "Voluntary services",
    "61831000000105": "Periodontics service",
    "893231000000108": "Podiatric surgery service",
    "893581000000109": "Well baby service",
    "893911000000106": "Paediatric gastrointestinal surgery service",
    "395104009": "Cancer primary healthcare multidisciplinary team",
    "892711000000104": "Gynaecological oncology service",
    "893331000000102": "Dementia assessment service",
    "892611000000105": "Hepatology service",
    "893681000000105": "Paediatric trauma and orthopaedics service",
    "395086005": "Community specialist palliative care",
    "395092004": "Specialist palliative care",
    "710028007": "Maxillofacial surgery service",
    "892811000000109": "Adult mental health service",
    "828821000000105": "Adolescent psychiatry service",
    "983341000000102": "Pharmacy First service",
    "893431000000109": "Trauma and orthopaedics service",
    "893781000000102": "Paediatric plastic surgery service",
    "892581000000104": "Learning disability service",
    "893661000000101": "Paediatric clinical haematology service",
    "893311000000105": "Haemophilia service",
    "373654008": "Medical referral service",
    "893081000000100": "Respiratory medicine service",
    "911221000000100": "Remote care environment monitoring service",
    "409971007": "Emergency medical services",
    "828371000000100": "Well man service",
    "963151000000104": "Diabetic medicine service",
    "893761000000106": "Paediatric rheumatology service",
    "932841000000106": "Public health dentistry service",
    "893861000000102": "Paediatric neurodisability service",
    "92191000000105": "Early intervention in psychosis team",
    "722424008": "Physical medicine and rehabilitation service",
    "89311000000105": "Crisis prevention assessment and treatment team",
    "722393008": "Legal medicine service",
    "722352000": "Vascular medicine service",
    "722170006": "Chiropractic service",
    "722174002": "Pulmonary medicine service",
    "722175001": "Psychosomatic medicine service",
    "722176000": "Dentistry service",
    "722140001": "Physiotherapy service",
    "892561000000108": "Medical ophthalmology service",
    "714088003": "Midwifery service",
    "714089006": "Community midwifery service",
    "3761000175103": "Pediatric endocrinology service",
    "893611000000103": "Paediatric epilepsy service",
    "893961000000108": "Paediatric cardiac surgery service",
    "931841000000103": "Oral microbiology service",
    "91901000000109": "Assertive outreach team",
    "828191000000104": "Dental hygiene service",
    "893031000000104": "Clinical immunology service",
    "893381000000103": "Clinical psychology service",
    "2461000175101": "Pulmonary rehabilitation service",
    "893161000000105": "Neurology service",
    "828201000000102": "Dental surgery assistance service",
    "1079491000000102": "Paediatric diabetes service",
    "893261000000103": "Mental health dual diagnosis service",
    "310031001": "Family planning service",
    "310032008": "Intensive care service",
    "310030000": "Endoscopy service",
    "310034009": "Pediatric intensive care service",
    "310033003": "Adult intensive care service",
    "310025004": "Complementary therapy service",
    "310024000": "Colposcopy service",
    "310027007": "Mental health counseling service",
    "310026003": "Counseling service",
    "310029005": "Domiciliary visit service",
    "310028002": "Diagnostic investigation service",
    "310020009": "Hearing therapy service",
    "310022001": "Clinical oncology service",
    "310021008": "Assistive listening device service",
    "310023006": "Radiotherapy service",
    "310017001": "Pediatric hearing aid service",
    "310016005": "Adult hearing aid service",
    "310015009": "Hearing aid service",
    "310014008": "Pediatric cochlear implant service",
    "310013002": "Adult cochlear implant service",
    "310012007": "Cochlear implant service",
    "310011000": "Aural rehabilitation service",
    "310010004": "Distraction test audiological screening service",
    "310019003": "Tinnitus management service",
    "310018006": "Speech-reading training service",
    "310001007": "Anesthetic service",
    "310000008": "Accident and Emergency service",
    "310003005": "Child assessment service",
    "310002000": "Assessment service",
    "310008001": "Audiological screening service",
    "310009009": "Neonatal audiological screening service",
    "310005003": "Diagnostic audiology service",
    "310004004": "Audiological service",
    "310007006": "Pediatric diagnostic audiology service",
    "310006002": "Adult diagnostic audiology service",
    "310085001": "Drama therapy service",
    "310086000": "Music therapy service",
    "310083008": "Art therapy service",
    "310082003": "Arts therapy services",
    "310084002": "Dance therapy service",
    "310089007": "Hospital-based podiatry service",
    "310087009": "Podiatry service",
    "310088004": "Community-based podiatry service",
    "310080006": "Pharmacy service",
    "310081005": "Professional allied to medicine service",
    "310079008": "Neuropathology service",
    "310078000": "Medical microbiology service",
    "310071006": "Pain management service",
    "310070007": "Special care baby service",
    "310072004": "Acute pain service",
    "310073009": "Palliative care service",
    "310076001": "Clinical biochemistry service",
    "310074003": "Pathology service",
    "310064001": "Occupational health service",
    "310063007": "Obstetrics service",
    "310066004": "Pediatric service",
    "310065000": "Open access service",
    "310068003": "Pediatric neurology service",
    "310067008": "Community pediatric service",
    "310069006": "Pediatric oncology service",
    "310061009": "Gynecology service",
    "310062002": "Pregnancy termination service",
    "310060005": "Obstetrics and gynecology service",
    "310099002": "Child physiotherapy service",
    "310098005": "Hospital-based physiotherapy service",
    "310091004": "Community-based dietetics service",
    "310090003": "Dietetics service",
    "310096009": "Hospital-based occupational therapy service",
    "310094007": "Community-based occupational therapy service",
    "310095008": "Social services occupational therapy service",
    "310093001": "Occupational therapy service",
    "310092006": "Hospital-based dietetics service",
    "310120006": "Mental handicap psychiatry service",
    "310121005": "Psychogeriatric service",
    "310126000": "Breast screening service",
    "310128004": "Computerized tomography service",
    "310127009": "Magnetic resonance imaging service",
    "310129007": "Rehabilitation service",
    "310122003": "Rehabilitation psychiatry service",
    "310123008": "Psychology service",
    "310124002": "Psychotherapy service",
    "310125001": "Radiology service",
    "310117003": "Child and adolescent psychiatry service",
    "310116007": "Psychiatry service",
    "310119000": "Liaison psychiatry service",
    "310118008": "Forensic psychiatry service",
    "310114005": "Community surgical fitting service",
    "310112009": "Surgical fitting service",
    "310115006": "Public health service",
    "310113004": "Hospital surgical fitting service",
    "310110001": "Hospital orthotics service",
    "310111002": "Community orthotics service",
    "310109006": "Orthotics service",
    "310108003": "Community orthoptics service",
    "310105000": "Optometry service",
    "310107008": "Hospital orthoptics service",
    "310106004": "Orthoptics service",
    "310104001": "Child speech and language therapy service",
    "310103007": "Hospital-based speech and language therapy service",
    "310102002": "Community-based speech and language therapy service",
    "310141000": "Thoracic surgery service",
    "310143002": "Dental surgery service",
    "310142007": "Cardiac surgery service",
    "310144008": "General dental surgery service",
    "310145009": "Oral surgery service",
    "310146005": "Orthodontics service",
    "310147001": "Pediatric dentistry service",
    "310148006": "Restorative dentistry service",
    "310149003": "Ear, nose and throat service",
    "310140004": "Cardiothoracic surgery service",
    "310131003": "Community rehabilitation service",
    "310130002": "Head injury rehabilitation service",
    "310134006": "Social services",
    "310135007": "Social services department customer services",
    "310132005": "Young disabled service",
    "310133000": "Swallow clinic",
    "310139001": "Breast surgery service",
    "310138009": "Surgical service",
    "310136008": "Social services department duty team",
    "310137004": "Stroke service",
    "310101009": "Speech and language therapy service",
    "310100005": "Play therapy service",
    "734862008": "Endodontic service",
    "734863003": "Prosthodontic service",
    "310168000": "Vascular surgery service",
    "310169008": "Ultrasonography service",
    "310165002": "Transplant surgery service",
    "310167005": "Urology service",
    "310166001": "Trauma surgery service",
    "310163009": "Pediatric surgical service",
    "310164003": "Plastic surgery service",
    "310161006": "Orthopedic service",
    "310162004": "Pancreatic surgery service",
    "310160007": "Ophthalmology service",
    "310151004": "Gastrointestinal surgery service",
    "310152006": "General gastrointestinal surgery service",
    "310153001": "Upper gastrointestinal surgery service",
    "310155008": "Colorectal surgery service",
    "310150003": "Endocrine surgery service",
    "310157000": "Hand surgery service",
    "310156009": "General surgical service",
    "310159002": "Neurosurgical service",
    "310158005": "Hepatobiliary surgical service",
    "828301000000108": "Electrocardiography service",
    "310200001": "Cytology service",
    "734920002": "Diabetes mellitus education service",
    "829951000000102": "Industrial therapy service",
    "931821000000105": "School nursing service",
    "893941000000107": "Paediatric dermatology service",
    "892741000000103": "Clinical microbiology service",
    "893211000000100": "Spinal injuries service",
    "92221000000103": "Mental health home treatment team",
    "3621000175101": "Rheumatology service",
    "408451000": "Community learning disabilities team",
    "408452007": "Behavioral intervention team",
    "408458006": "Specialist multidisciplinary team",
    "893341000000106": "Congenital heart disease service",
    "445449000": "Acute care hospice service",
    "1078501000000104": "Health visiting service",
    "893691000000107": "Paediatric transplantation surgery service",
    "892621000000104": "Hepatobiliary and pancreatic surgery service",
    "2421000175108": "Acute care inpatient service",
    "931801000000101": "Community nursing service",
    "699478002": "Surgical oncology service",
    "893791000000100": "Paediatric pain management service",
    "893541000000101": "Prosthetics service",
    "699650006": "Community based physiotherapy service",
    "893891000000108": "Paediatric interventional radiology service",
    "827631000000105": "Emergency ambulance service",
    "827981000000103": "Paediatric cystic fibrosis service",
    "892821000000103": "Critical care medicine service",
    "700435004": "Clinical physiology service",
    "700436003": "Clinical pharmacology service",
    "700434000": "Endocrinology service",
    "700221004": "Care of elderly service",
    "700433006": "Gastroenterology service",
    "700231006": "Critical care physician service",
    "700232004": "General medical service",
    "700241009": "Dermatology service",
    "893061000000109": "Cardiology service",
    "705150003": "Domiciliary physiotherapy service",
    "932241000000105": "Blood banking and transfusion service",
    "3791000175107": "Pediatric nephrology service",
    "892791000000108": "Blood and marrow transplantation service",
    "893641000000102": "Palliative medicine service",
    "431051000124102": "Dialysis service",
    "23951000087100": "Opioid dependence service",
    "1323651000000109": "Cardiac physiology service",
    "788126001": "Prosthetic service",
    "788124003": "Histopathology service",
    "788125002": "Addiction service",
    "788123009": "Radiation oncology service",
    "788122004": "Sexual health service",
    "788128000": "Critical care medicine service",
    "788127005": "Child health service",
    "788121006": "Clinical immunology and allergy service",
    "733921009": "Transplant medicine service",
    "788001008": "Infectious disease service",
    "788002001": "Adult mental health service",
    "788003006": "Nephrology service",
    "788009005": "Nuclear medicine service",
    "788006003": "Genetic laboratory service",
    "788004000": "Clinical genetics service",
    "788005004": "Neurology service",
    "788008002": "Oral and maxillofacial surgery service",
    "788007007": "General practice service",
    "1326391000000100": "FNP (Family Nurse Partnership) service",
    "1186717003": "Intellectual disability psychiatry service",
    "830149003": "Clinical neurophysiology service",
    "224930009": "Services",
    "830039004": "Genitourinary medicine service",
    "830038007": "Clinical allergy service",
    "830037002": "Clinical immunology service",
    "1326421000000106": "Safeguarding children team",
    "1323551000000105": "Inherited metabolic medicine service",
    "28541000087101": "Musculoskeletal service",
    "24271000087103": "Adult chronic pain management service",
    "1240241000000109": "Community sexual and reproductive health service",
    "897188002": "Pediatric hematology service",
    "1323631000000102": "Aviation and space medicine service",
    "1325831000000100": "Post-COVID-19 syndrome service",
    "1323431000000104": "Fetal medicine service",
    "24001000087103": "Paediatric plastic surgery service",
    "24351000087104": "Paediatric chronic pain management service",
    "1323881000000102": "Stroke medicine service",
    "1323531000000103": "Urological physiology service",
    "148621000000100": "School aged immunisation service",
    "24101000087102": "HIV (human immunodeficiency virus) social work service",
    "23911000087104": "Medication review service",
    "1148679005": "Specialist palliative care service",
    "773558007": "Physical medicine service",
    "24051000087102": "Breast surgical oncology service",
    "896974005": "Transgender health service",
    "1323611000000105": "Paediatric inherited metabolic medicine service",
    "1323661000000107": "Paediatric audiovestibular medicine service",
    "24331000087108": "Narcotic addiction service with chronic pain management",
    "1323561000000108": "Gastrointestinal physiology service",
    "34911000087100": "Amputation care service",
    "1231786003": "Refugee healthcare service",
    "1163002007": "Electrocardiography service",
    "1163004008": "Hyperbaric medicine service",
    "1163003002": "Colorectal cancer screening service",
    "1323841000000105": "Paediatric palliative medicine service",
    "1163054002": "Gastroscopy service",
    "1231392007": "Paediatric orthopaedic service",
    "1231391000": "Colonoscopy service",
    "1231393002": "Spirometry service",
    "1231390004": "Hand therapy service",
    "1231394008": "Paediatric urology service",
    "24081000087105": "HIV (human immunodeficiency virus) nurse practitioner service",
    "23941000087103": "Narcotic addiction service",
    "1323641000000106": "Audiovestibular medicine service",
    "840587001": "Aerospace medical service",
    "840586005": "Neonatal service",
    "840585009": "Postnatal service",
    "816075004": "Prosthetic and orthotic service",
    "1323921000000108": "Neuropsychiatry service",
    "24011000087101": "Vascular imaging service",
    "1323691000000101": "General internal medical service",
    "23891000087102": "Adult hematology service",
    "1323821000000103": "Paediatric clinical pharmacology service",
    "789718008": "Cardiology service",
    "789714005": "Pediatric rheumatology service",
    "789715006": "Paediatric respiratory therapy service",
    "789716007": "Pediatric otolaryngology service",
    "789717003": "Paediatric cardiology service",
    "148581000000100": "Personal health record provider service",
    "792849008": "Pediatric clinical genetics service",
    "792847005": "Emergency ambulance service",
    "792848000": "Internal medicine service",
    "1323621000000104": "Medical psychotherapy service",
    "1323871000000104": "Rehabilitation medicine service",
    "1230046007": "Cervical cancer screening service",
    "1230045006": "Cardiac diagnostic service",
    "1230044005": "Cardiac specialist nursing service",
    "1362761000000103": "Adult safeguarding team",
    "1323901000000104": "Rare disease service",
    "1136421000168109": "Sleep medicine service",
    "1323701000000101": "Vascular physiology service",
    "24141000087104": "Spine orthopedic surgery service",
    "1323571000000101": "Orthogeriatric medicine service",
    "1323801000000107": "Paediatric oral and maxillofacial surgery service",
    "23871000087101": "Adult dermatology service",
    "1323601000000108": "Ophthalmic and vision science service",
    "1234796008": "Community nursing service",
    "23901000087101": "Hepatology service",
    "1324191000000107": "Intensive care medicine service",
    "2391000175104": "Bariatric surgery service",
    "1323851000000108": "Paediatric hepatology service",
    "24291000087104": "Geriatric chronic pain management service",
    "1323501000000109": "Special care dentistry service",
    "1423561000000102": "Acute oncology service",
    "394802001": "General medicine",
}


SYSTEM_SHORT_IDS = {"http://snomed.info/sct": "SCT", "https://nicip.nhs.uk": "NICIP"}
CONTENT_STABILITY_EXTENSION_URL = (
    "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-ContentStability"
)
CONTENT_STABILITY_SYSTEM_URL = (
    "https://fhir.nhs.uk/England/CodeSystem/England-NRLContentStability"
)
CONTENT_FORMAT_CODE_URL = "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode"
CONTENT_FORMAT_CODE_MAP = {
    "urn:nhs-ic:record-contact": "Contact details (HTTP Unsecured)",
    "urn:nhs-ic:unstructured": "Unstructured Document",
    "urn:nhs-ic:structured": "Structured Document",
}

ATTACHMENT_CONTENT_TYPES = {
    "application/pdf",
    "text/html",
    "application/json",
    "application/fhir+json",
    "application/json+fhir",
}
