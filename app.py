from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'edupath-secret-2026')

# ─────────────────────────────────────────────
# CLIENTS DB  (PostgreSQL — shared across dev & production)
# ─────────────────────────────────────────────
def get_pg():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def init_clients_db():
    conn = get_pg()
    conn.cursor().execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id         SERIAL PRIMARY KEY,
            name       TEXT NOT NULL,
            email      TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_clients_db()

def get_client_by_email(email):
    conn = get_pg()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM clients WHERE email = %s', (email,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def save_client(name, email):
    try:
        conn = get_pg()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO clients (name, email)
            VALUES (%s, %s)
            ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name
        ''', (name, email))
        conn.commit()
        conn.close()
        app.logger.info(f"save_client OK: {email}")
    except Exception as e:
        app.logger.error(f"save_client ERROR for {email}: {e}")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'client_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────
# COURSES  (college students, 12 per stream)
# ─────────────────────────────────────────────
COLLEGE_COURSES = {
    "Commerce & Management": [
        {"id": "bba",         "name": "BBA – Bachelor of Business Administration"},
        {"id": "bcom_hons",   "name": "B.Com (Hons) – Commerce Honours"},
        {"id": "bcom",        "name": "B.Com – Bachelor of Commerce"},
        {"id": "bms",         "name": "BMS – Bachelor of Management Studies"},
        {"id": "ba_econ",     "name": "BA (Hons) Economics"},
        {"id": "ipm",         "name": "Integrated MBA (IPM) – 5 Year Program"},
        {"id": "bba_llb",     "name": "BBA-LLB (Hons) – Business & Law"},
        {"id": "bfia",        "name": "BFIA – Finance & Investment Analysis"},
        {"id": "ba_biz_econ", "name": "BA Business Economics"},
        {"id": "bbm",         "name": "BBM – Bachelor of Business Management"},
        {"id": "bcom_af",     "name": "B.Com (Accounting & Finance)"},
        {"id": "bsc_econ",    "name": "B.Sc Economics (Hons)"},
    ],
    "Engineering & Technology": [
        {"id": "btech_cse",      "name": "B.Tech – Computer Science & Engineering"},
        {"id": "btech_ece",      "name": "B.Tech – Electronics & Communication Engineering"},
        {"id": "btech_mech",     "name": "B.Tech – Mechanical Engineering"},
        {"id": "btech_eee",      "name": "B.Tech – Electrical Engineering"},
        {"id": "btech_civil",    "name": "B.Tech – Civil Engineering"},
        {"id": "btech_it",       "name": "B.Tech – Information Technology"},
        {"id": "btech_aiml",     "name": "B.Tech – Artificial Intelligence & Machine Learning"},
        {"id": "btech_ds",       "name": "B.Tech – Data Science & Engineering"},
        {"id": "btech_chem",     "name": "B.Tech – Chemical Engineering"},
        {"id": "btech_aero",     "name": "B.Tech – Aerospace & Aeronautical Engineering"},
        {"id": "btech_robotics", "name": "B.Tech – Robotics & Automation"},
        {"id": "btech_cyber",    "name": "B.Tech – Cybersecurity & Ethical Hacking"},
    ],
    "Humanities & Social Sciences": [
        {"id": "ba_ir",        "name": "BA (Hons) – International Relations"},
        {"id": "ba_pols",      "name": "BA (Hons) – Political Science"},
        {"id": "ba_sociology", "name": "BA (Hons) – Sociology"},
        {"id": "ba_psych",     "name": "BA (Hons) – Psychology"},
        {"id": "ba_econ_h",    "name": "BA (Hons) – Economics"},
        {"id": "ba_history",   "name": "BA (Hons) – History"},
        {"id": "ba_english",   "name": "BA (Hons) – English Literature"},
        {"id": "ba_jmc",       "name": "BA – Journalism & Mass Communication"},
        {"id": "ba_llb",       "name": "BA-LLB (Hons) – Integrated Law (5 Year)"},
        {"id": "bsw",          "name": "BSW – Bachelor of Social Work"},
        {"id": "ba_geo",       "name": "BA (Hons) – Geography & Environment"},
        {"id": "ba_phil",      "name": "BA (Hons) – Philosophy"},
    ],
    "Medicine & Life Sciences": [
        {"id": "mbbs",        "name": "MBBS – Bachelor of Medicine & Surgery"},
        {"id": "bds",         "name": "BDS – Bachelor of Dental Surgery"},
        {"id": "bpharm",      "name": "B.Pharm – Bachelor of Pharmacy"},
        {"id": "bsc_nursing", "name": "B.Sc Nursing"},
        {"id": "bams",        "name": "BAMS – Ayurvedic Medicine & Surgery"},
        {"id": "bhms",        "name": "BHMS – Homeopathic Medicine & Surgery"},
        {"id": "bpt",         "name": "BPT – Bachelor of Physiotherapy"},
        {"id": "bsc_biotech", "name": "B.Sc – Biotechnology"},
        {"id": "bsc_biochem", "name": "B.Sc – Biochemistry"},
        {"id": "bsc_micro",   "name": "B.Sc – Microbiology"},
        {"id": "bmlt",        "name": "BMLT – Medical Lab Technology"},
        {"id": "bsc_nutri",   "name": "B.Sc – Nutrition & Dietetics"},
    ],
    "Design & Creative Arts": [
        {"id": "bdes_product",   "name": "B.Des – Industrial & Product Design"},
        {"id": "bdes_comm",      "name": "B.Des – Communication & Graphic Design"},
        {"id": "bdes_fashion",   "name": "B.Des – Fashion Design"},
        {"id": "bdes_textile",   "name": "B.Des – Textile & Surface Design"},
        {"id": "bdes_ux",        "name": "B.Des – UX / Interaction Design"},
        {"id": "bdes_animation", "name": "B.Des – Animation & Game Design"},
        {"id": "barch",          "name": "B.Arch – Bachelor of Architecture"},
        {"id": "bfa",            "name": "BFA – Bachelor of Fine Arts"},
        {"id": "bsc_interior",   "name": "B.Sc – Interior Design"},
        {"id": "bdes_jewellery", "name": "B.Des – Jewellery & Accessory Design"},
        {"id": "bftech",         "name": "B.F.Tech – Fashion Technology"},
        {"id": "bsc_photo",      "name": "B.Sc – Photography & Visual Media"},
    ],
}

# ─────────────────────────────────────────────
# SPECIALIZATIONS  (per course id)
# ─────────────────────────────────────────────
SPECIALIZATIONS = {
    "bba": ["Marketing & Brand Management", "Finance & Investment Banking",
            "Human Resources Management", "International Business",
            "Entrepreneurship & Startup Ecosystem", "Digital Marketing & E-Commerce",
            "Supply Chain & Logistics Management", "Business Analytics & Intelligence",
            "Healthcare & Hospital Management", "Operations & Project Management",
            "Retail & Consumer Goods Management", "Family Business Management"],
    "bcom_hons": ["Taxation & Indirect Tax", "Accounting & Auditing",
                  "Banking, Finance & Insurance", "Financial Markets & Securities",
                  "Corporate Law & Compliance", "E-Commerce & Digital Business"],
    "bcom": ["General Commerce", "Taxation", "Accounting & Finance", "Banking & Insurance"],
    "bms": ["Marketing", "Finance", "Human Resources", "International Business", "Entrepreneurship"],
    "ba_econ": ["Development Economics", "Financial Economics", "International Trade & Policy",
                "Econometrics & Data Analysis", "Public Policy & Governance", "Environmental Economics"],
    "ipm": ["General Management", "Finance & Strategic Management",
            "Marketing & Consumer Behaviour", "Operations & Supply Chain",
            "Human Resources & Organisational Behaviour", "Business Analytics & AI"],
    "bba_llb": ["Corporate & Commercial Law", "International Trade & Investment Law",
                "Intellectual Property Rights (IPR)", "Taxation & Financial Law",
                "Dispute Resolution & Arbitration"],
    "bfia": ["Equity Research & Valuation", "Portfolio & Wealth Management",
             "Risk & Compliance Management", "FinTech & Algorithmic Trading"],
    "ba_biz_econ": ["Micro & Macro Economics", "Business Statistics & Modelling", "Finance & Capital Markets"],
    "bbm": ["Marketing", "Finance", "HR Management", "Retail Management", "Operations"],
    "bcom_af": ["Financial Accounting", "Corporate Finance", "Auditing & Assurance", "Taxation & GST"],
    "bsc_econ": ["Quantitative Economics", "Policy & Welfare Economics", "Development Economics"],
    "btech_cse": ["Artificial Intelligence & Machine Learning", "Cybersecurity & Ethical Hacking",
                  "Cloud Computing & DevOps", "Data Science & Big Data Analytics",
                  "Full-Stack Web Development", "Blockchain & Distributed Systems",
                  "Internet of Things (IoT)", "Game Development & Interactive Media",
                  "Computer Vision & NLP", "Software Engineering & Architecture"],
    "btech_ece": ["VLSI Design & Embedded Systems", "Signal Processing & Communications",
                  "Wireless & Mobile Networks", "Robotics & Mechatronics",
                  "Telecommunications Engineering", "Microelectronics & Nanotechnology"],
    "btech_mech": ["Automotive Engineering", "Manufacturing & Production Engineering",
                   "Thermal & Fluid Dynamics", "Design Engineering (CAD/CAE/FEA)",
                   "Robotics & Mechatronics", "Industrial & Systems Engineering"],
    "btech_eee": ["Power Systems & Smart Grid", "Control Systems & Automation",
                  "Renewable & Green Energy", "Electric Vehicles & EV Technology",
                  "Industrial Drives & Power Electronics"],
    "btech_civil": ["Structural Engineering", "Transportation & Highway Engineering",
                    "Environmental & Water Resources Engineering",
                    "Construction Project Management", "Geotechnical Engineering"],
    "btech_it": ["Software Development & Engineering", "Network & Systems Administration",
                 "Cybersecurity & Privacy", "Data Analytics & Business Intelligence",
                 "Cloud Infrastructure & SRE"],
    "btech_aiml": ["Deep Learning & Neural Networks", "Natural Language Processing (NLP)",
                   "Computer Vision & Image Processing", "Reinforcement & Autonomous Learning",
                   "AI Ethics, Policy & Governance", "MLOps & AI Infrastructure at Scale"],
    "btech_ds": ["Business Intelligence & Analytics", "Big Data Engineering",
                 "Statistical & Predictive Modelling", "Data Visualisation & Storytelling",
                 "Healthcare Data Science"],
    "btech_chem": ["Petrochemical & Refinery Engineering", "Pharmaceutical Process Engineering",
                   "Food Technology & Safety", "Environmental & Green Chemistry",
                   "Process Simulation & Control"],
    "btech_aero": ["Aerodynamics & Flight Mechanics", "Jet Propulsion & Turbomachinery",
                   "Avionics & Flight Systems", "Aircraft Structural Design",
                   "Space Technology & Orbital Mechanics"],
    "btech_robotics": ["Industrial Automation & PLC", "AI-Powered Autonomous Robots",
                       "Human-Robot Interaction (HRI)", "Medical & Surgical Robotics",
                       "Drone & UAV Systems"],
    "btech_cyber": ["Ethical Hacking & Penetration Testing", "Network Security & Cryptography",
                    "Digital Forensics & Incident Response", "Application & Web Security",
                    "Cloud & Container Security"],
    "ba_ir": ["Diplomacy & Foreign Policy", "Strategic Studies & National Security",
              "International Trade & Investment Law", "Global Governance & UN Studies",
              "South Asian & Regional Studies", "European & Transatlantic Studies",
              "Development Cooperation & Aid Policy"],
    "ba_pols": ["Comparative Politics & Systems", "Indian Politics & Governance",
                "International Politics & Theory", "Public Policy & Administration",
                "Electoral & Democratic Studies"],
    "ba_sociology": ["Social Research Methods", "Gender & Women's Studies",
                     "Urban & Rural Sociology", "Development & Poverty Studies",
                     "Cultural & Media Studies"],
    "ba_psych": ["Clinical & Counselling Psychology", "Organisational & Industrial Psychology",
                 "Neuropsychology & Cognitive Science", "Sports & Performance Psychology",
                 "Child & Developmental Psychology", "Health Psychology & Behavioural Medicine"],
    "ba_econ_h": ["Development & Welfare Economics", "Financial & Capital Markets Economics",
                  "International Trade Economics", "Econometrics & Applied Statistics",
                  "Public Finance & Governance"],
    "ba_history": ["Ancient & Medieval History", "Modern & Contemporary World History",
                   "Art History & Cultural Heritage", "Military & Diplomatic History",
                   "Colonial & Post-Colonial Studies"],
    "ba_english": ["Literary Studies & Critical Theory", "Creative Writing & Screenwriting",
                   "Linguistics & Applied Language Studies", "Post-Colonial Literature",
                   "Film Studies & Media Criticism"],
    "ba_jmc": ["Print & Investigative Journalism", "Broadcast & Television Journalism",
               "Digital Media & Social Journalism", "Public Relations & Corporate Communications",
               "Film & Documentary Making", "Photojournalism & Visual Storytelling"],
    "ba_llb": ["Corporate & Commercial Law", "Constitutional & Administrative Law",
               "Criminal Law & Criminology", "International Trade & Investment Law",
               "Intellectual Property Rights (IPR)", "Environmental & Human Rights Law"],
    "bsw": ["Community Development & Welfare", "Child Protection & Family Services",
            "Mental Health Social Work", "Healthcare & Medical Social Work",
            "NGO & Non-Profit Management"],
    "ba_geo": ["Urban Planning & Smart Cities", "Environmental & Climate Change Studies",
               "Remote Sensing, GIS & Cartography", "Economic Geography & Trade"],
    "ba_phil": ["Ethics & Moral Philosophy", "Political & Social Philosophy",
                "Eastern & Comparative Philosophy", "Philosophy of Science & Mind"],
    "mbbs": ["General Medicine & Internal Medicine", "Surgery & Operative Sciences",
             "Paediatrics & Neonatology", "Cardiology & Cardiothoracic Surgery",
             "Neurology & Neurosurgery", "Orthopaedics & Trauma Surgery",
             "Obstetrics & Gynaecology", "Dermatology, Venereology & Cosmetology",
             "Diagnostic Radiology & Imaging Sciences", "Psychiatry & Mental Health",
             "Emergency & Critical Care Medicine", "Oncology & Radiation Therapy"],
    "bds": ["Oral & Maxillofacial Surgery", "Orthodontics & Dentofacial Orthopaedics",
            "Periodontology & Implantology", "Cosmetic & Aesthetic Dentistry",
            "Paediatric Dentistry"],
    "bpharm": ["Clinical Pharmacy & Therapeutics", "Industrial Pharmacy & Drug Manufacturing",
               "Pharmacology & Drug Discovery", "Hospital & Retail Pharmacy",
               "Regulatory Affairs & Quality Assurance"],
    "bsc_nursing": ["Critical & ICU Care Nursing", "Paediatric & Neonatal Nursing",
                    "Community & Public Health Nursing", "Psychiatric & Mental Health Nursing",
                    "Midwifery & Gynaecological Nursing"],
    "bams": ["Kayachikitsa (Internal Medicine)", "Shalya Tantra (Surgery)",
             "Panchakarma & Detox Therapy", "Dravyaguna (Ayurvedic Pharmacology)",
             "Prasuti Tantra (Obs & Gynaecology)"],
    "bhms": ["Classical Homoeopathic Practice", "Homoeopathic Pharmacy & Materia Medica",
             "Paediatric Homoeopathy", "Psychiatric & Behavioural Homoeopathy"],
    "bpt": ["Neurological Physiotherapy", "Orthopaedic & Sports Physiotherapy",
            "Paediatric Physiotherapy", "Cardiopulmonary Physiotherapy",
            "Rehabilitation Sciences & Prosthetics"],
    "bsc_biotech": ["Genetic Engineering & Genomics", "Industrial & Environmental Biotechnology",
                    "Medical & Pharmaceutical Biotechnology", "Agricultural Biotechnology",
                    "Bioinformatics & Computational Biology", "Stem Cell & Regenerative Medicine"],
    "bsc_biochem": ["Metabolic & Structural Biochemistry", "Clinical Biochemistry & Diagnostics",
                    "Proteomics & Structural Biology", "Enzymology & Molecular Biology"],
    "bsc_micro": ["Medical & Clinical Microbiology", "Industrial & Food Microbiology",
                  "Virology & Epidemiology", "Environmental & Agricultural Microbiology"],
    "bmlt": ["Haematology & Blood Banking", "Clinical Microbiology & Serology",
             "Clinical Biochemistry & Endocrinology", "Histopathology & Cytology"],
    "bsc_nutri": ["Clinical Nutrition & Medical Dietetics", "Sports & Performance Nutrition",
                  "Community & Public Health Nutrition", "Food Science, Safety & Technology"],
    "bdes_product":   ["Human-Centred Product Design", "Automotive & Transportation Design",
                       "Furniture & Space Design", "Medical Device & Healthcare Design",
                       "Sustainable & Circular Design", "Consumer Electronics Design"],
    "bdes_comm":      ["Brand Identity & Visual Communication", "Motion Graphics & Video Design",
                       "Editorial & Publication Design", "Advertising & Art Direction",
                       "Packaging Design", "Digital Media & Web Design"],
    "bdes_fashion":   ["Luxury & Couture Fashion", "Sustainable & Ethical Fashion",
                       "Ready-to-Wear & Retail Design", "Accessories & Footwear Design",
                       "Fashion Styling & Curation", "Kidswear & Maternity Design"],
    "bdes_textile":   ["Surface Ornamentation & Crafts", "Knitwear & Weave Design",
                       "Textile Technology & Innovation", "Digital Print & Dye",
                       "Handloom & Heritage Crafts"],
    "bdes_ux":        ["Mobile & App UX Design", "User Research & Usability Testing",
                       "Service & Systems Design", "Voice & Conversational UI",
                       "Design Thinking & Innovation Strategy"],
    "bdes_animation": ["2D & 3D Character Animation", "Visual Effects (VFX) & Compositing",
                       "Game Concept & Level Design", "Motion Graphics & Title Design",
                       "Augmented & Virtual Reality (AR/VR)"],
    "barch":          ["Sustainable & Green Architecture", "Urban Design & City Planning",
                       "Interior Architecture & Adaptive Reuse", "Landscape Architecture",
                       "Heritage Conservation & Restoration", "Digital Fabrication & Parametric Design"],
    "bfa":            ["Painting & Mixed Media", "Sculpture & Ceramics",
                       "Printmaking & Graphic Arts", "Photography & New Media Art",
                       "Performance & Video Art"],
    "bsc_interior":   ["Residential Interior Design", "Commercial & Corporate Interiors",
                       "Hospitality & Retail Design", "Sustainable Interior Design", "Lighting Design"],
    "bdes_jewellery": ["Fine Jewellery & Goldsmithing", "Contemporary & Concept Jewellery",
                       "Gemology & Diamond Grading", "Accessories & Leather Goods"],
    "bftech":         ["Apparel Manufacturing Technology", "Textile Testing & Quality Assurance",
                       "Supply Chain & Merchandising", "Fashion CAD & Pattern Making"],
    "bsc_photo":      ["Commercial & Advertising Photography", "Documentary & Photojournalism",
                       "Fashion & Portrait Photography", "Film & Cinematography"],
}

# ─────────────────────────────────────────────
# SCHOOL SUBJECTS  (per stream)
# ─────────────────────────────────────────────
SCHOOL_SUBJECTS = {
    "Commerce & Management": {
        "options": [
            "Accountancy", "Business Studies", "Economics",
            "Applied Mathematics", "Informatics Practices", "Entrepreneurship"
        ],
        "optional": [
            "Physical Education", "NCC", "Music (Carnatic/Hindustani/Percussion)",
            "Dance", "Artificial Intelligence", "Data Science", "Tourism", "Mass Media"
        ],
        "required": ["English Core"],
        "note": "English Core is pre-selected. Choose your stream subjects and any optional/skill subjects you like."
    },
    "Engineering & Technology": {
        "options": [
            "Physics", "Chemistry", "Mathematics", "Biology",
            "Computer Science", "Biotechnology", "Engineering Graphics"
        ],
        "optional": [
            "Physical Education", "NCC", "Music (Carnatic/Hindustani/Percussion)",
            "Dance", "Artificial Intelligence", "Data Science", "Tourism", "Mass Media"
        ],
        "required": ["English Core"],
        "note": "English Core is pre-selected. Choose your stream subjects and any optional/skill subjects you like."
    },
    "Humanities & Social Sciences": {
        "options": [
            "History", "Geography", "Political Science", "Psychology",
            "Sociology", "Legal Studies", "Home Science", "Fine Arts"
        ],
        "optional": [
            "Physical Education", "NCC", "Music (Carnatic/Hindustani/Percussion)",
            "Dance", "Artificial Intelligence", "Data Science", "Tourism", "Mass Media"
        ],
        "required": ["English Core"],
        "note": "English Core is pre-selected. Choose your stream subjects and any optional/skill subjects you like."
    },
    "Medicine & Life Sciences": {
        "options": [
            "Physics", "Chemistry", "Biology", "Mathematics",
            "Computer Science", "Biotechnology", "Engineering Graphics"
        ],
        "optional": [
            "Physical Education", "NCC", "Music (Carnatic/Hindustani/Percussion)",
            "Dance", "Artificial Intelligence", "Data Science", "Tourism", "Mass Media"
        ],
        "required": ["English Core"],
        "note": "English Core is pre-selected. Choose your stream subjects and any optional/skill subjects you like."
    },
    "Design & Creative Arts": {
        "options": [
            "Fine Arts / Drawing", "Applied Arts", "History of Art",
            "Photography", "Craft & Textile Design", "Mass Media & Communication"
        ],
        "optional": [
            "Computer Aided Design", "Music", "Dance", "Digital Art & Animation",
            "Theatre Arts", "Physical Education", "NCC", "Tourism"
        ],
        "required": ["English Core"],
        "note": "English Core is pre-selected. Choose your arts/design subjects and any creative optional subjects."
    },
}

COURSE_FALLBACK = {
    "bcom": "bcom_hons", "bms": "bba", "ba_biz_econ": "ba_econ",
    "bba_llb": "ba_llb", "bfia": "bcom_hons", "bbm": "bba",
    "bcom_af": "bcom_hons", "bsc_econ": "ba_econ",
    "btech_eee": "btech_mech", "btech_civil": "btech_mech",
    "btech_it": "btech_cse", "btech_ds": "btech_aiml",
    "btech_chem": "btech_mech", "btech_aero": "btech_mech",
    "btech_robotics": "btech_ece", "btech_cyber": "btech_cse",
    "ba_pols": "ba_ir", "ba_sociology": "ba_ir", "ba_history": "ba_ir",
    "bdes_textile": "bdes_product", "bdes_ux": "bdes_comm",
    "bdes_animation": "bdes_comm", "bfa": "bdes_comm",
    "bsc_interior": "barch", "bdes_jewellery": "bdes_fashion",
    "bftech": "bdes_fashion", "bsc_photo": "bdes_comm",
    "ba_english": "ba_ir", "bsw": "ba_psych", "ba_geo": "ba_ir",
    "ba_phil": "ba_ir", "ba_econ_h": "ba_econ",
    "bds": "mbbs", "bsc_nursing": "mbbs", "bams": "mbbs", "bhms": "mbbs",
    "bsc_biochem": "bsc_biotech", "bsc_micro": "bsc_biotech",
    "bmlt": "bsc_biotech", "bsc_nutri": "bpt",
}

STREAM_ICONS = {
    "Commerce & Management":        "📊",
    "Engineering & Technology":     "⚙️",
    "Humanities & Social Sciences": "🌍",
    "Medicine & Life Sciences":     "🩺",
    "Design & Creative Arts":       "🎨",
}

# Entrance exams per course key — india vs abroad
COURSE_EXAMS = {
    # ── Commerce & Management ──
    "bba":         {"india": ["IPMAT (IIM)", "NPAT (NMIMS)", "DU JAT / CUET", "SET (Symbiosis)", "BHU UET", "Christ Univ. Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "GMAT (integrated)", "AP Exams"]},
    "bcom_hons":   {"india": ["CUET", "DU JAT", "IPMAT", "Christ Univ. Entrance", "BHU UET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Exams"]},
    "bcom":        {"india": ["CUET", "DU JAT", "Christ Univ. Entrance", "MJPRU Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "bms":         {"india": ["DUJAT / CUET", "Mumbai Univ. CET", "SET (Symbiosis)", "Christ Univ. Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "ba_econ":     {"india": ["CUET", "DU JAT", "JNU Entrance", "BHU UET", "Presidency Univ. Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Economics"]},
    "ipm":         {"india": ["IPMAT (IIM Indore)", "JIPMAT (IIM Ranchi/Bodh Gaya)", "NPAT (NMIMS)", "SET (Symbiosis)"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "GMAT (integrated)"]},
    "bba_llb":     {"india": ["CLAT", "AILET", "LSAT India", "SLAT (Symbiosis)", "BVP CET"],
                    "abroad": ["LSAT", "SAT / ACT", "IELTS / TOEFL"]},
    "bfia":        {"india": ["DU JAT / CUET", "IPMAT", "NPAT"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "ba_biz_econ": {"india": ["CUET", "DU JAT", "Christ Univ. Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "bbm":         {"india": ["CUET", "KCET (Bangalore Univ.)", "Christ Univ. Entrance", "Jain Univ. Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "bcom_af":     {"india": ["CUET", "Mumbai Univ. CET", "Christ Univ. Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "bsc_econ":    {"india": ["CUET", "JNU Entrance", "BHU UET", "AMU Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Economics"]},
    # ── Engineering & Technology ──
    "btech_cse":   {"india": ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "SRMJEEE", "MET (Manipal)", "COMEDK", "WBJEE", "MHT CET", "KCET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "A-Levels / IB", "AP Computer Science"]},
    "btech_ece":   {"india": ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "SRMJEEE", "MET", "COMEDK", "WBJEE", "MHT CET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "A-Levels / IB", "AP Physics"]},
    "btech_mech":  {"india": ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "SRMJEEE", "MET", "COMEDK", "WBJEE", "MHT CET", "KCET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "A-Levels / IB"]},
    "btech_eee":   {"india": ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "SRMJEEE", "MET", "COMEDK", "MHT CET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "A-Levels / IB"]},
    "btech_civil": {"india": ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "COMEDK", "WBJEE", "MHT CET", "KCET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "A-Levels / IB"]},
    "btech_it":    {"india": ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "SRMJEEE", "MET", "COMEDK", "MHT CET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Computer Science"]},
    "btech_aiml":  {"india": ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "SRMJEEE", "MET", "COMEDK", "MHT CET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Computer Science", "AP Statistics"]},
    "btech_ds":    {"india": ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "SRMJEEE", "MHT CET", "COMEDK"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Statistics", "AP Computer Science"]},
    "btech_chem":  {"india": ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "MET", "COMEDK", "MHT CET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Chemistry"]},
    "btech_aero":  {"india": ["JEE Main", "JEE Advanced", "BITSAT", "SRMJEEE", "VITEEE", "MET", "MHT CET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "A-Levels Physics/Maths"]},
    "btech_robotics": {"india": ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "SRMJEEE", "MET", "COMEDK"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Physics", "AP Computer Science"]},
    "btech_cyber": {"india": ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "SRMJEEE", "MET", "MHT CET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Computer Science"]},
    # ── Humanities & Social Sciences ──
    "ba_psych":    {"india": ["CUET", "DU Entrance", "Christ Univ. Entrance", "Fergusson Entrance", "BHU UET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Psychology"]},
    "ba_ir":       {"india": ["CUET", "DU Entrance", "JNU Entrance", "SET (Symbiosis)", "Jamia Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "A-Levels / IB"]},
    "ba_pols":     {"india": ["CUET", "DU Entrance", "JNU Entrance", "BHU UET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "ba_sociology":{"india": ["CUET", "DU Entrance", "JNU Entrance", "Tata Inst. (TISS-NET)"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "ba_history":  {"india": ["CUET", "DU Entrance", "JNU Entrance", "BHU UET", "AMU Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP World History"]},
    "ba_english":  {"india": ["CUET", "DU Entrance", "BHU UET", "JNU Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP English Literature"]},
    "ba_jmc":      {"india": ["IIMC Entrance", "Symbiosis SIMC", "IPU CET", "XIC Entrance", "CUET", "ACJ Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "Portfolio / Writing Sample"]},
    "ba_llb":      {"india": ["CLAT", "AILET", "LSAT India", "DU LLB Entrance", "MH CET Law", "SLAT"],
                    "abroad": ["LSAT", "SAT / ACT", "IELTS / TOEFL"]},
    "bsw":         {"india": ["TISS-NET", "CUET", "DU Entrance", "Jamia Entrance", "IGNOU Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "ba_geo":      {"india": ["CUET", "DU Entrance", "JNU Entrance", "BHU UET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "ba_phil":     {"india": ["CUET", "JNU Entrance", "DU Entrance", "BHU UET"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Philosophy (IB)"]},
    # ── Medicine & Life Sciences ──
    "mbbs":        {"india": ["NEET UG", "AIIMS (via NEET)", "JIPMER (via NEET)", "State METs"],
                    "abroad": ["NEET UG (mandatory for India-recognised degrees)", "IELTS / TOEFL", "USMLE (USA)", "PLAB (UK)", "AMC (Australia)"]},
    "bds":         {"india": ["NEET UG"],
                    "abroad": ["NEET UG (mandatory)", "IELTS / TOEFL"]},
    "bpharm":      {"india": ["CUET", "MHT CET", "KCET", "WBJEE", "TS EAMCET", "AP EAMCET", "Chandigarh Univ. Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Chemistry / Biology"]},
    "bsc_nursing": {"india": ["NEET UG (some colleges)", "AIIMS BSc Nursing", "CUET", "JIPMER BSc Nursing", "State Nursing Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "NCLEX (USA post-degree)"]},
    "bams":        {"india": ["NEET UG"],
                    "abroad": ["NEET UG (mandatory)", "IELTS / TOEFL"]},
    "bhms":        {"india": ["NEET UG"],
                    "abroad": ["NEET UG (mandatory)", "IELTS / TOEFL"]},
    "bpt":         {"india": ["CUET", "MHT CET", "KCET", "IPU CET", "College-specific Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "bsc_biotech": {"india": ["CUET", "JNU Entrance", "BHU UET", "Jamia Entrance", "JNUEE", "AMU Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Biology / Chemistry"]},
    "bsc_biochem": {"india": ["CUET", "JNU Entrance", "BHU UET", "Presidency Univ. Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Biology / Chemistry"]},
    "bsc_micro":   {"india": ["CUET", "JNU Entrance", "BHU UET", "AMU Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Biology"]},
    "bmlt":        {"india": ["CUET", "IPU CET", "MHT CET", "College-specific Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "bsc_nutri":   {"india": ["CUET", "BHU UET", "AMU Entrance", "Symbiosis SET", "Lady Irwin Entrance"],
                    "abroad": ["SAT / ACT", "IELTS / TOEFL", "AP Biology"]},
    # ── School student general keys ──
    "school_commerce":   {"india": ["CUET", "IPMAT (IIM)", "NPAT", "DU JAT", "CLAT (Law)", "SET (Symbiosis)"],
                          "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "school_engineering":{"india": ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "SRMJEEE", "MHT CET", "KCET", "WBJEE"],
                          "abroad": ["SAT / ACT", "IELTS / TOEFL", "A-Levels / IB"]},
    "school_humanities": {"india": ["CUET", "DU Entrance", "JNU Entrance", "CLAT", "IIMC Entrance", "TISS-NET"],
                          "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "school_medical":    {"india": ["NEET UG", "AIIMS (via NEET)", "JIPMER (via NEET)", "CUET (Pharmacy/Nursing)"],
                          "abroad": ["NEET UG (mandatory)", "SAT / ACT", "IELTS / TOEFL", "USMLE (USA)"]},
    "bdes_product":   {"india": ["NID DAT", "UCEED (IIT)", "MITID DAT", "Srishti Entrance", "Pearl Academy Entrance"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL", "Portfolio Review"]},
    "bdes_comm":      {"india": ["NID DAT", "NIFT CAT+GAT", "UCEED (IIT)", "Srishti Entrance", "Pearl Academy Entrance"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL", "Portfolio Review"]},
    "bdes_fashion":   {"india": ["NIFT Entrance (CAT+GAT)", "NID DAT", "Pearl Academy Entrance", "FDDI Entrance"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL", "Portfolio Review"]},
    "bdes_textile":   {"india": ["NIFT CAT+GAT", "NID DAT", "Pearl Academy Entrance", "FDDI Entrance"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL", "Portfolio Review"]},
    "bdes_ux":        {"india": ["NID DAT", "UCEED (IIT)", "Srishti Entrance", "MITID DAT"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL", "Portfolio Review"]},
    "bdes_animation": {"india": ["NID DAT", "NIFT CAT+GAT", "UCEED", "Srishti Entrance"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL", "Portfolio Review"]},
    "barch":          {"india": ["JEE Main (Paper 2A)", "NATA", "CUET", "MHT CET", "KCET Architecture", "AP EAMCET"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL", "Portfolio Review", "RIBA-accredited entry"]},
    "bfa":            {"india": ["BHU UET (Fine Arts)", "CUET", "DU Entrance", "MSU Baroda Entrance"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL", "Portfolio Review"]},
    "bsc_interior":   {"india": ["NID DAT", "Pearl Academy Entrance", "Symbiosis SET", "MITID DAT"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL", "Portfolio Review"]},
    "bdes_jewellery": {"india": ["NID DAT", "NIFT CAT+GAT", "Pearl Academy Entrance"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL", "Portfolio Review"]},
    "bftech":         {"india": ["NIFT Entrance (CAT+GAT)", "FDDI Entrance", "CUET"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL"]},
    "bsc_photo":      {"india": ["JMI Entrance", "Srishti Entrance", "CUET", "Pearl Academy Entrance"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL", "Portfolio Review"]},
    "school_design":  {"india": ["NID DAT", "NIFT CAT+GAT", "UCEED", "NATA", "Srishti Entrance", "Pearl Academy Entrance"],
                       "abroad": ["SAT / ACT", "IELTS / TOEFL", "Portfolio Review"]},
}

def annotate_colleges_with_exams(colleges):
    """Add 'exams' string to each college dict using COURSE_EXAMS lookup."""
    for col in colleges:
        key = col.get('course_key', '')
        region = col.get('region', 'India')
        exam_entry = COURSE_EXAMS.get(key, {})
        exam_list = exam_entry.get('india' if region == 'India' else 'abroad', [])
        col['exams'] = ', '.join(exam_list)
    return colleges

SCHOOL_KEY_MAP = {
    "Commerce & Management":        "school_commerce",
    "Engineering & Technology":     "school_engineering",
    "Humanities & Social Sciences": "school_humanities",
    "Medicine & Life Sciences":     "school_medicine",
    "Design & Creative Arts":       "school_design",
}


# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────
def build_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""CREATE TABLE colleges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_key TEXT, name TEXT, region TEXT, location TEXT, rank TEXT, fees TEXT, features TEXT
    )""")
    c.execute("""CREATE TABLE careers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT, stream TEXT, region TEXT, title TEXT, salary TEXT, outlook TEXT, duties TEXT
    )""")

    colleges = [
        # ── SCHOOL COLLEGES ──────────────────────────────────────
        ("school_commerce","The Doon School, Dehradun","India","Dehradun, India","#1 National Boarding","₹12–14 Lakhs/Yr","Elite alumni network; outstanding university placement cell."),
        ("school_commerce","La Martiniere for Boys, Kolkata","India","Kolkata, India","Top Tier Day School","₹1.5–2 Lakhs/Yr","Legendary legacy; outstanding commerce and economics department."),
        ("school_commerce","DPS R.K. Puram, New Delhi","India","Delhi, India","Top Academic Rank","₹2–3 Lakhs/Yr","Consistently produces national board toppers in commerce."),
        ("school_commerce","St. Xavier's Collegiate School, Kolkata","India","Kolkata, India","Top Historic Day School","₹1–1.5 Lakhs/Yr","Rigorous academic tradition; excellent foundational accounting."),
        ("school_commerce","Campion School, Mumbai","India","Mumbai, India","#1 Day School West India","₹2–3 Lakhs/Yr","Stellar management infrastructure and early leadership tracking."),
        ("school_commerce","Phillips Academy Andover","Abroad","Massachusetts, USA","#1 US Boarding","$65,000/Yr","Ivy League prep powerhouse; sophisticated global economics track."),
        ("school_commerce","Eton College, Windsor","Abroad","London, UK","#1 UK Historic Boarding","£46,000/Yr","Educates global leaders; premier financial history infrastructure."),
        ("school_commerce","Raffles Institution, Singapore","Abroad","Singapore","#1 Singapore Public","$15,000/Yr","Unrivalled Asian academic standards; fast-track to global finance."),
        ("school_commerce","Charterhouse School, UK","Abroad","London, UK","Elite UK Boarding","£44,000/Yr","World-famous economics and business operations modules."),
        ("school_commerce","Trinity College School, Canada","Abroad","Ontario, Canada","#1 Canada Boarding","$55,000/Yr","Exceptional global university preparation and leadership labs."),
        ("school_engineering","DPS R.K. Puram, New Delhi","India","Delhi, India","#1 Competitive Exam Prep","₹2–3 Lakhs/Yr","Stellar system for IIT-JEE top ranks and advanced science."),
        ("school_engineering","DAV Boys Sr Secondary, Chennai","India","Chennai, India","Top South India Rank","₹80,000/Yr","Known for hyper-focused mathematical and engineering minds."),
        ("school_engineering","FIITJEE Junior College, Hyderabad","India","Hyderabad, India","Top Specialised Engineering","₹3–4 Lakhs/Yr","Curriculum strictly optimised for competitive entrance matrices."),
        ("school_engineering","National Public School (NPS), Bangalore","India","Bangalore, India","Silicon Valley Pipeline","₹1.5–2.5 Lakhs/Yr","Excellent CS integration built into secondary schooling."),
        ("school_engineering","Bombay Scottish School, Mumbai","India","Mumbai, India","Top Academic ICSE","₹1.5–2 Lakhs/Yr","Rigorous analytics; highly advanced physics and maths labs."),
        ("school_engineering","Stuyvesant High School, New York","Abroad","New York, USA","#1 US Public STEM","Free (Merit Exam)","Highly selective; home to Nobel laureates and tech founders."),
        ("school_engineering","Westminster School, London","Abroad","London, UK","#1 UK Academic","£43,000/Yr","Unrivalled pipeline into Oxford and Cambridge engineering."),
        ("school_engineering","Thomas Jefferson HS for Science & Tech","Abroad","Virginia, USA","#1 US STEM Academy","Free (Merit Exam)","State-of-the-art supercomputing and aerospace labs."),
        ("school_engineering","Hwa Chong Institution, Singapore","Abroad","Singapore","Elite Singapore STEM","$12,000/Yr","Global powerhouse for Maths and Physics Olympiad training."),
        ("school_engineering","The Bronte College, Canada","Abroad","Ontario, Canada","Top Canada Science","$48,000/Yr","Accelerated AP/IB tracks for international engineering admissions."),
        ("school_humanities","Welham Girls' School, Dehradun","India","Dehradun, India","#1 Girls Boarding School","₹10–12 Lakhs/Yr","Produces exceptional liberal arts candidates and policy thinkers."),
        ("school_humanities","Step by Step School, Noida","India","Noida, India","Top Modern Infrastructure","₹3–4 Lakhs/Yr","Political science and psychology lab modules for projects."),
        ("school_humanities","Sanskriti School, New Delhi","India","Delhi, India","Civil Services Feeder","₹1.5–2.5 Lakhs/Yr","Preferred by diplomats and top-tier civil service families."),
        ("school_humanities","Loreto House, Kolkata","India","Kolkata, India","Top Historic Humanities","₹1 Lakh/Yr","Centuries-old reputation in English literature and sociology."),
        ("school_humanities","The Sanskaar Valley School, Bhopal","India","Bhopal, India","Top Central Region","₹2.5–3.5 Lakhs/Yr","Exceptional theatre, history debate and public speaking setup."),
        ("school_humanities","Phillips Exeter Academy","Abroad","New Hampshire, USA","Elite US Harkness System","$62,000/Yr","Harkness discussion method — ideal for advanced political study."),
        ("school_humanities","Harrow School, London","Abroad","London, UK","Elite UK Tradition","£45,000/Yr","Premier historical archives and global leadership track."),
        ("school_humanities","UWC South East Asia","Abroad","Singapore","#1 IB Global Profile","$40,000/Yr","Hyper-diverse cohort on international policy and human rights."),
        ("school_humanities","Upper Canada College","Abroad","Ontario, Canada","Top Canada Liberal Arts","$58,000/Yr","Stellar philosophy and global history for university placement."),
        ("school_humanities","Ecole Nouvelle de la Suisse Romande","Abroad","Lausanne, Switzerland","Elite Switzerland Profile","CHF 75,000/Yr","Multilingual diplomatic training in the heart of Europe."),
        ("school_medicine","Sri Chaitanya Institutions, Vijayawada","India","Vijayawada, India","#1 NEET Pipeline","₹2.5–4 Lakhs/Yr","Produces the bulk of top ranks in national pre-medical entry."),
        ("school_medicine","Allen Career Institute, Kota","India","Kota, India","World's Largest Medical Academy","₹1.5–3 Lakhs/Yr","Definitive hub for competitive pre-medical chemistry training."),
        ("school_medicine","Resonance, Kota","India","Kota, India","Top Competitive Hub","₹1.5–2.5 Lakhs/Yr","Rigorous doubt-clearing with sophisticated medical mock analytics."),
        ("school_medicine","Modern School Barakhamba, New Delhi","India","Delhi, India","Top Legacy Infrastructure","₹2–3 Lakhs/Yr","Exceptional biotechnology and advanced biochemistry labs."),
        ("school_medicine","St. John's High School, Chandigarh","India","Chandigarh, India","Top North India Academy","₹1–1.5 Lakhs/Yr","Stellar record in advanced biological sciences study."),
        ("school_medicine","Boston Latin School","Abroad","Boston, USA","Historic US Pre-Med Academy","Free (Merit)","America's oldest public school; connections to Harvard Medical."),
        ("school_medicine","St Paul's School, London","Abroad","London, UK","Elite UK Medical Track","£42,000/Yr","Advanced organic chemistry labs that outpace many universities."),
        ("school_medicine","Raffles Girls' School, Singapore","Abroad","Singapore","Top Singapore Life Sciences","$14,000/Yr","State-of-the-art genetic modelling equipment built in."),
        ("school_medicine","Columbia International College, Canada","Abroad","Ontario, Canada","Top Canada Life Sciences","$45,000/Yr","Accelerated pre-medical tracks linked to North American systems."),
        ("school_medicine","The King's School, Canterbury","Abroad","London, UK","Elite UK Bio-Sciences","£43,000/Yr","Strong institutional links with leading European clinical research."),
        # ── BBA ──────────────────────────────────────────────────
        ("bba","Christ University, Bangalore","India","Bangalore, India","#1 BBA in India","₹2.0–2.5 Lakhs/Yr","Industry-embedded BBA with live corporate projects and strong placements."),
        ("bba","Symbiosis Institute of Business Management, Pune","India","Pune, India","Top BBA Private","₹3.0–3.5 Lakhs/Yr","Rigorous global business curriculum; excellent international exposure."),
        ("bba","NMIMS School of Business Management, Mumbai","India","Mumbai, India","Top West India BBA","₹3.2–4.0 Lakhs/Yr","Strong case-study pedagogy; outstanding finance and marketing placements."),
        ("bba","Shaheed Sukhdev College of Business Studies, DU","India","Delhi, India","Top Government BBA","₹20,000–30,000/Yr","Premier DU college; elite alumni dominating Indian corporates."),
        ("bba","Narsee Monjee College, Mumbai","India","Mumbai, India","Top Mumbai Rank","₹1.0–1.5 Lakhs/Yr","Strong Bombay Stock Exchange and banking sector placements."),
        ("bba","Wharton School, University of Pennsylvania","Abroad","Philadelphia, USA","#1 US Undergrad Business","$65,000/Yr","Absolute pinnacle of undergraduate business; unrivalled alumni network."),
        ("bba","IE Business School, Madrid","Abroad","Madrid, Spain","#1 European BBA","€29,000/Yr","Entrepreneurship-first BBA; remarkable global diversity and VC access."),
        ("bba","ESCP Business School, Paris-London","Abroad","Paris, France","Top Triple-Accredited EU","€19,000/Yr","Multi-campus BBA across 6 European cities; global business immersion."),
        ("bba","Nanyang Business School, NTU Singapore","Abroad","Singapore","#1 Asia-Pacific BBA","$22,000/Yr","Dual-degree options; strong Asia-Pacific corporate linkages."),
        ("bba","University of Melbourne (Commerce)","Abroad","Melbourne, Australia","#1 Australia Business","$38,000/Yr","World-class finance, marketing and entrepreneurship programmes."),
        # ── B.COM HONS ───────────────────────────────────────────
        ("bcom_hons","Shri Ram College of Commerce (SRCC), Delhi","India","Delhi, India","#1 Commerce in Asia","₹25,000–30,000/Yr","Gold standard for B.Com; perfect consulting/finance placements."),
        ("bcom_hons","Loyola College, Chennai","India","Chennai, India","Top Southern Hub","₹40,000–50,000/Yr","Exceptional corporate relations and brilliant accounting depth."),
        ("bcom_hons","St. Xavier's College, Mumbai","India","Mumbai, India","Elite Western Legacy","₹20,000–30,000/Yr","Highly selective; alumni dominating Dalal Street and Big-4."),
        ("bcom_hons","Hansraj College, Delhi University","India","Delhi, India","Top DU Commerce","₹15,000–25,000/Yr","Strong placements in banking, insurance, and financial services."),
        ("bcom_hons","Jesus & Mary College, Delhi","India","Delhi, India","Top Women's Commerce DU","₹12,000–20,000/Yr","Exceptional academic rigour; consistent DU-topper production."),
        ("bcom_hons","London School of Economics (LSE)","Abroad","London, UK","#1 Global Accounting","£28,000/Yr","Unrivalled prestige; recruiting hub for Wall Street and London banks."),
        ("bcom_hons","University of Edinburgh Business School","Abroad","Edinburgh, UK","Top UK Commerce","£23,000/Yr","Strong quantitative finance; excellent Edinburgh finance alumni."),
        ("bcom_hons","University of Melbourne","Abroad","Melbourne, Australia","#1 Australia Commerce","$38,000/Yr","World-class actuarial, accounting, and corporate finance courses."),
        ("bcom_hons","NTU Nanyang Business School, Singapore","Abroad","Singapore","#1 Asia Commerce","$22,000/Yr","Premier Asian accounting and finance destination."),
        ("bcom_hons","University of Toronto (Rotman)","Abroad","Toronto, Canada","#1 Canada Commerce","$42,000/Yr","Premier gateway to North American banking and corporate finance."),
        # ── BA ECONOMICS ─────────────────────────────────────────
        ("ba_econ","SRCC Delhi (BA Economics)","India","Delhi, India","#1 Economics Delhi","₹25,000/Yr","Pipeline for top consulting, IES and MBA programmes in India."),
        ("ba_econ","Lady Shri Ram College, Delhi","India","Delhi, India","#1 Women's Economics DU","₹15,000–20,000/Yr","Outstanding political economy and development economics track."),
        ("ba_econ","Presidency University, Kolkata","India","Kolkata, India","Top Historic Economics","₹10,000–15,000/Yr","Legendary economics department producing top researchers and IAS."),
        ("ba_econ","Ashoka University, Sonipat","India","Sonipat, India","Top Liberal Arts Economics","₹12–14 Lakhs/Yr","Cutting-edge liberal arts economics with strong research output."),
        ("ba_econ","Indian Statistical Institute (ISI), Kolkata","India","Kolkata, India","#1 Quantitative Economics","₹10,000–15,000/Yr","Globally ranked; pipeline for research, RBI, and academia."),
        ("ba_econ","Harvard University","Abroad","Cambridge, USA","#1 Global Economics","$68,000/Yr","World presidents and Nobel laureates; definitive economics apex."),
        ("ba_econ","London School of Economics (LSE)","Abroad","London, UK","#1 UK Economics","£28,000/Yr","Largest economics faculty globally; unmatched policy research."),
        ("ba_econ","University of Chicago","Abroad","Chicago, USA","#1 Economic Theory","$65,000/Yr","Home of the Chicago School; 33 Nobel Laureates in Economics."),
        ("ba_econ","Sciences Po, Paris","Abroad","Paris, France","#1 European Policy Econ","€15,000/Yr","Premier economic policy and governance track in Europe."),
        ("ba_econ","Princeton University","Abroad","Princeton, USA","Top Ivy Economics","$66,000/Yr","Woodrow Wilson School pipeline for economic policy and research."),
        # ── INTEGRATED MBA (IPM) ─────────────────────────────────
        ("ipm","IIM Indore (IPM)","India","Indore, India","#1 IPM in India","₹16–18 Lakhs/Yr","Founding IPM programme; exceptional placement with top MNCs and consulting."),
        ("ipm","IIM Rohtak (IPM)","India","Rohtak, India","Top New-Gen IIM IPM","₹12–14 Lakhs/Yr","Strong analytics-focused IPM curriculum; good consulting placements."),
        ("ipm","IIM Ranchi (IPM)","India","Ranchi, India","Top IPM East India","₹10–12 Lakhs/Yr","Specialised HR and operations tracks; strong industry linkages."),
        ("ipm","IIM Jammu (IPM)","India","Jammu, India","Growing IIM IPM","₹8–10 Lakhs/Yr","Modern curriculum with digital business focus; excellent faculty."),
        ("ipm","NMIMS Mumbai (BBA-MBA Integrated)","India","Mumbai, India","Top Private IPM Equivalent","₹14–16 Lakhs/Yr","Strong finance and marketing dual-specialisation programme."),
        ("ipm","Wharton School, UPenn","Abroad","Philadelphia, USA","#1 US Integrated Business","$65,000/Yr","Absolute summit of integrated business and management education."),
        ("ipm","INSEAD, France/Singapore","Abroad","Paris, France","#1 Global MBA Programme","€90,000/Yr","World's most international business school; extraordinary network."),
        ("ipm","Kellogg School of Management, Northwestern","Abroad","Chicago, USA","#1 US Marketing MBA","$65,000/Yr","Top marketing and leadership management curriculum globally."),
        ("ipm","London Business School (LBS)","Abroad","London, UK","#1 European Business","£48,000/Yr","Prime access to EMEA corporate finance and consulting sectors."),
        ("ipm","HEC Paris","Abroad","Paris, France","#1 French Grande École","€50,000/Yr","European luxury goods, consulting, and investment banking pipeline."),
        # ── B.TECH CSE ───────────────────────────────────────────
        ("btech_cse","IIT Bombay","India","Mumbai, India","#1 National Technical","₹2.5 Lakhs/Yr","Ultimate dream destination; massive incubation and elite global offers."),
        ("btech_cse","IIT Delhi","India","Delhi, India","#2 National Technical","₹2.4 Lakhs/Yr","Elite computing infrastructure; primary startup hub location."),
        ("btech_cse","IIT Madras","India","Chennai, India","#1 NIRF Engineering","₹2.5 Lakhs/Yr","India's largest research park; global deep-tech leader."),
        ("btech_cse","IIIT Hyderabad","India","Hyderabad, India","#1 Specialised CS College","₹2.5–3.0 Lakhs/Yr","Pure CS focus; extraordinary research and product engineering output."),
        ("btech_cse","BITS Pilani","India","Pilani, India","#1 Private Engineering","₹6.0 Lakhs/Yr","Zero attendance policy; multi-million dollar startup ecosystem."),
        ("btech_cse","Massachusetts Institute of Technology (MIT)","Abroad","Cambridge, USA","#1 Global Tech","$64,000/Yr","Absolute epicentre of CS innovation and advanced AI architectures."),
        ("btech_cse","Stanford University","Abroad","Stanford, USA","#2 Global Tech","$66,000/Yr","Foundation engine of Silicon Valley; unparalleled VC access."),
        ("btech_cse","Carnegie Mellon University (CMU)","Abroad","Pittsburgh, USA","#1 Software Engineering","$60,000/Yr","World leader in robotics, computational logic, and cybernetics."),
        ("btech_cse","UC Berkeley (EECS)","Abroad","Berkeley, USA","#1 Public Global Tech","$48,000/Yr","Pioneered open-source tech; stellar decentralised web research."),
        ("btech_cse","ETH Zurich","Abroad","Zurich, Switzerland","#1 Continental Europe Tech","$3,000/Yr","Einstein's alma mater; incredible tech infrastructure at low cost."),
        # ── B.TECH ECE ───────────────────────────────────────────
        ("btech_ece","IIT Madras (ECE)","India","Chennai, India","#1 ECE in India","₹2.5 Lakhs/Yr","Exceptional signal processing, VLSI, and communications research."),
        ("btech_ece","IIT Delhi (ECE)","India","Delhi, India","Top ECE IIT","₹2.4 Lakhs/Yr","Premier semiconductor and embedded systems programme in India."),
        ("btech_ece","NIT Surathkal (ECE)","India","Mangalore, India","#1 NIT for ECE","₹1.5–2.0 Lakhs/Yr","Strong VLSI design and wireless communications curriculum."),
        ("btech_ece","BITS Pilani (ECE)","India","Pilani, India","Top Private ECE","₹6.0 Lakhs/Yr","Excellent ECE + CS dual-degree; great industry research links."),
        ("btech_ece","PSG College of Technology, Coimbatore","India","Coimbatore, India","Top South ECE","₹1.5–2.5 Lakhs/Yr","Strong industry-academia collaboration and hardware design labs."),
        ("btech_ece","MIT (EECS)","Abroad","Cambridge, USA","#1 Global ECE","$64,000/Yr","Definitive global home for semiconductor and communications R&D."),
        ("btech_ece","Stanford (EE)","Abroad","Stanford, USA","#2 Global ECE","$66,000/Yr","Silicon Valley epicentre for chip design and wireless tech."),
        ("btech_ece","Imperial College London","Abroad","London, UK","#1 UK ECE","£35,000/Yr","Top-tier European centre for signal processing and RF engineering."),
        ("btech_ece","NTU Singapore","Abroad","Singapore","#1 Asia-Pacific ECE","$22,000/Yr","World-class semiconductor and photonics research ecosystem."),
        ("btech_ece","TU Delft, Netherlands","Abroad","Delft, Netherlands","#1 European ECE","€2,200/Yr","Globally renowned for microelectronics and embedded systems."),
        # ── B.TECH MECHANICAL ────────────────────────────────────
        ("btech_mech","IIT Bombay (Mech)","India","Mumbai, India","#1 Mechanical IIT","₹2.5 Lakhs/Yr","Premier thermal-fluid and manufacturing research in India."),
        ("btech_mech","IIT Kanpur (Mech)","India","Kanpur, India","Top Mech IIT","₹2.4 Lakhs/Yr","Excellent aerospace + mechanical cross-disciplinary research."),
        ("btech_mech","IIT Kharagpur (Mech)","India","Kharagpur, India","Top Legacy Mechanical","₹2.3 Lakhs/Yr","Oldest IIT; renowned automotive and industrial engineering output."),
        ("btech_mech","NIT Trichy (Mech)","India","Trichy, India","#1 NIT Mechanical","₹1.5–2.0 Lakhs/Yr","Consistent top placements in core manufacturing and auto sector."),
        ("btech_mech","VIT Vellore (Mech)","India","Vellore, India","Top Private Mechanical","₹1.8–2.5 Lakhs/Yr","Strong industry tie-ups with Tata, Bosch, Hyundai, and Mahindra."),
        ("btech_mech","MIT (MechE)","Abroad","Cambridge, USA","#1 Global Mechanical","$64,000/Yr","Defines modern mechanical engineering innovation globally."),
        ("btech_mech","ETH Zurich (MechE)","Abroad","Zurich, Switzerland","#1 European Mechanical","$3,000/Yr","Exceptional robotics, mechatronics and manufacturing research."),
        ("btech_mech","TU Munich (Mechanical)","Abroad","Munich, Germany","Top German Engineering","€1,500/Yr","Industry-academia powerhouse; BMW, Siemens, and MAN connections."),
        ("btech_mech","Imperial College London (MechE)","Abroad","London, UK","#1 UK Mechanical","£35,000/Yr","Outstanding Formula 1, aerospace, and robotics engineering track."),
        ("btech_mech","University of Michigan, Ann Arbor","Abroad","Ann Arbor, USA","#1 US Automotive Mech","$50,000/Yr","Premier automotive engineering; Ford and GM recruiting hub."),
        # ── B.TECH AI/ML ─────────────────────────────────────────
        ("btech_aiml","IIT Hyderabad (AI)","India","Hyderabad, India","#1 Dedicated AI IIT","₹2.5 Lakhs/Yr","First IIT to offer standalone B.Tech in AI; cutting-edge research."),
        ("btech_aiml","IIT Bombay (AI/DS)","India","Mumbai, India","Top AI IIT Bombay","₹2.5 Lakhs/Yr","World-class deep learning, NLP, and computer vision research."),
        ("btech_aiml","IIIT Hyderabad (AI)","India","Hyderabad, India","Top Specialised AI Institute","₹2.5–3.0 Lakhs/Yr","Industry-leading AI research; strong FAANG placement track."),
        ("btech_aiml","BITS Pilani (AI/ML Minor)","India","Pilani, India","Top Private AI","₹6.0 Lakhs/Yr","Flexible dual-degree allows deep AI + domain specialisation."),
        ("btech_aiml","VIT Vellore (AI & DS)","India","Vellore, India","Top Private AI Growth","₹1.8–2.5 Lakhs/Yr","Large AI research centre; strong global university tie-ups."),
        ("btech_aiml","Carnegie Mellon University (AI)","Abroad","Pittsburgh, USA","#1 Global AI","$60,000/Yr","The founding home of AI as a discipline; unmatched research depth."),
        ("btech_aiml","Stanford (CS — AI Track)","Abroad","Stanford, USA","#2 Global AI","$66,000/Yr","Hub of AI industry transformation; direct line to top labs."),
        ("btech_aiml","Massachusetts Institute of Technology","Abroad","Cambridge, USA","Top AI & ML Globally","$64,000/Yr","CSAIL lab: most cited AI research institution in the world."),
        ("btech_aiml","University of Toronto","Abroad","Toronto, Canada","Birthplace of Deep Learning","$48,000/Yr","Geoff Hinton's home; Vector Institute AI ecosystem hub."),
        ("btech_aiml","TU Munich (AI)","Abroad","Munich, Germany","#1 European AI","€1,500/Yr","Leading applied AI research; BMW, Siemens, and MunichRe AI labs."),
        # ── BA INTERNATIONAL RELATIONS ───────────────────────────
        ("ba_ir","Jawaharlal Nehru University (JNU), Delhi","India","Delhi, India","#1 IR & Global Policy","₹1,000–2,000/Yr","Unparalleled political discourse; extraordinary international security output."),
        ("ba_ir","Lady Shri Ram College (LSR), Delhi","India","Delhi, India","#1 Liberal Arts IR Focus","₹15,000–25,000/Yr","Produces peak UN delegates and international policy chiefs."),
        ("ba_ir","Jadavpur University, Kolkata","India","Kolkata, India","Top Public Arts Hub","₹3,000–5,000/Yr","World-renowned comparative international relations department."),
        ("ba_ir","O.P. Jindal Global University, Sonipat","India","Sonipat, India","Top Private IR","₹8–12 Lakhs/Yr","Modern IR curriculum; strong MUN, internship and global exposure."),
        ("ba_ir","Symbiosis School of International Studies, Pune","India","Pune, India","Top Private IR Hub","₹3.5–4.5 Lakhs/Yr","Geopolitics, economic corridors and simulated war-gaming."),
        ("ba_ir","Harvard University","Abroad","Cambridge, USA","#1 Global IR & Policy","$68,000/Yr","Educates world presidents and global geopolitical strategists."),
        ("ba_ir","Sciences Po, Paris","Abroad","Paris, France","#1 European Diplomacy","€15,000/Yr","Definitive European governance and bilingual IR track."),
        ("ba_ir","Georgetown University (Walsh School)","Abroad","Washington DC, USA","#1 Washington DC Policy","$61,000/Yr","Directly linked with embassies and the Pentagon in DC."),
        ("ba_ir","Graduate Institute (IHEID), Geneva","Abroad","Geneva, Switzerland","#1 Global Security Hub","CHF 5,000/Yr","Integrated into the UN in Geneva; immediate internship access."),
        ("ba_ir","Australian National University (ANU)","Abroad","Canberra, Australia","#1 Asia-Pacific Strategy","$38,000/Yr","Definitive authority on Asia-Pacific defence and maritime law."),
        # ── BA PSYCHOLOGY ────────────────────────────────────────
        ("ba_psych","Lady Shri Ram College (LSR), Delhi","India","Delhi, India","#1 Psychology Women's","₹15,000–25,000/Yr","Exceptional developmental and clinical psychology curriculum."),
        ("ba_psych","Christ University, Bangalore","India","Bangalore, India","Top Private Psychology","₹1.5–2.0 Lakhs/Yr","Strong counselling, clinical and organisational psychology tracks."),
        ("ba_psych","Fergusson College, Pune","India","Pune, India","Top Autonomous Psychology","₹25,000–40,000/Yr","Long-standing psychology faculty; strong Pune research ecosystem."),
        ("ba_psych","Tata Institute of Social Sciences (TISS), Mumbai","India","Mumbai, India","#1 Applied Psychology","₹80,000/Yr","Outstanding mental health, HR and social psychology programmes."),
        ("ba_psych","Amity University, Noida","India","Noida, India","Top Private Psychology","₹2.0–3.0 Lakhs/Yr","Modern clinical labs; tie-ups with hospitals for placements."),
        ("ba_psych","Harvard University (Psychology)","Abroad","Cambridge, USA","#1 Global Psychology","$68,000/Yr","Premier cognitive science, clinical, and developmental research."),
        ("ba_psych","University College London (UCL)","Abroad","London, UK","#1 UK Psychology","£24,000/Yr","Top BPS-accredited programme; exceptional neuroscience links."),
        ("ba_psych","University of Melbourne","Abroad","Melbourne, Australia","#1 Australia Psychology","$38,000/Yr","Outstanding accredited clinical and research psychology pathway."),
        ("ba_psych","University of Amsterdam","Abroad","Amsterdam, Netherlands","Top European Psychology","€2,200/Yr","World leader in social and cognitive psychology research."),
        ("ba_psych","University of Edinburgh","Abroad","Edinburgh, UK","Top UK Psychology","£23,000/Yr","Excellent neuropsychology and health psychology departments."),
        # ── BA JOURNALISM & MASS COMMUNICATION ──────────────────
        ("ba_jmc","IIMC (Indian Institute of Mass Communication), Delhi","India","Delhi, India","#1 Journalism India","₹50,000–80,000/Yr","Premier journalism institution; alumni run top Indian newsrooms."),
        ("ba_jmc","Jamia Millia Islamia, Delhi (AJK MCRC)","India","Delhi, India","Top Public JMC","₹30,000–50,000/Yr","Excellent broadcast and digital media labs; strong media placements."),
        ("ba_jmc","Symbiosis Institute of Media & Communication, Pune","India","Pune, India","Top Private JMC","₹3.5–4.5 Lakhs/Yr","Strong industry visits, internships and advertising industry links."),
        ("ba_jmc","Xavier Institute of Communications, Mumbai","India","Mumbai, India","Top XIC Mumbai","₹2.5–3.5 Lakhs/Yr","Outstanding media management and PR curriculum; Mumbai media access."),
        ("ba_jmc","Manipal Institute of Communication","India","Manipal, India","Top Deemed University JMC","₹2.0–3.0 Lakhs/Yr","Integrated media programmes; strong TV, film and digital media labs."),
        ("ba_jmc","Columbia University Graduate School of Journalism","Abroad","New York, USA","#1 Global Journalism","$65,000/Yr","Pulitzer Prize institution; definitive US investigative journalism."),
        ("ba_jmc","Northwestern Medill School of Journalism","Abroad","Chicago, USA","#1 US Undergrad JMC","$63,000/Yr","Exceptional data journalism and immersive journalism programmes."),
        ("ba_jmc","London School of Economics (Media & Comm)","Abroad","London, UK","#1 UK Media Studies","£28,000/Yr","Critical media theory and digital communications excellence."),
        ("ba_jmc","Cardiff University, School of Journalism","Abroad","Cardiff, UK","Top UK Broadcast JMC","£22,000/Yr","Top-ranked UK journalism; BBC Wales and Channel 4 partnerships."),
        ("ba_jmc","New York University (NYU Journalism)","Abroad","New York, USA","Top NYC Journalism","$63,000/Yr","Excellent investigative reporting; access to New York media giants."),
        # ── BA-LLB (LAW) ─────────────────────────────────────────
        ("ba_llb","NLSIU Bangalore (National Law School)","India","Bangalore, India","#1 Law School India","₹2.5–3.0 Lakhs/Yr","India's premier NLU; pipeline to Supreme Court and top law firms."),
        ("ba_llb","NALSAR Hyderabad","India","Hyderabad, India","#2 Law School India","₹2.0–2.5 Lakhs/Yr","Exceptional human rights, corporate and international law faculty."),
        ("ba_llb","NLU Delhi (NLUD)","India","Delhi, India","#3 Law School India","₹2.5–3.0 Lakhs/Yr","Top NLU for corporate law; Delhi High Court and SC access."),
        ("ba_llb","O.P. Jindal Global Law School","India","Sonipat, India","#1 Private Law School","₹8–12 Lakhs/Yr","Largest law school by faculty; strong ADR and international law."),
        ("ba_llb","NLU Jodhpur (MNLU)","India","Jodhpur, India","Top Law NLU","₹1.5–2.5 Lakhs/Yr","Excellent corporate law, IP, and taxation specialisation tracks."),
        ("ba_llb","Harvard Law School","Abroad","Cambridge, USA","#1 Global Law","$68,000/Yr","Produces world's most influential attorneys and policymakers."),
        ("ba_llb","University of Oxford (Law)","Abroad","Oxford, UK","#2 Global Law","£30,000/Yr","BCL jurisprudence and international law tradition is unmatched."),
        ("ba_llb","Yale Law School","Abroad","New Haven, USA","#1 US Law (Rankings)","$67,000/Yr","Smallest but highest-ranked US law school; unrivalled faculty."),
        ("ba_llb","University of Cambridge (Law)","Abroad","Cambridge, UK","Top UK Law","£30,000/Yr","Strong common law tradition; barristers and solicitors pipeline."),
        ("ba_llb","NYU School of Law","Abroad","New York, USA","#1 US International Law","$65,000/Yr","Premier US destination for international law and global justice."),
        # ── MBBS ─────────────────────────────────────────────────
        ("mbbs","AIIMS New Delhi","India","Delhi, India","#1 Medical National","₹1,700 TOTAL","Absolute pinnacle of Indian medicine; massive clinical exposure."),
        ("mbbs","Christian Medical College (CMC), Vellore","India","Vellore, India","#2 National Medical","₹50,000/Yr","World-class community healthcare and stellar diagnostic labs."),
        ("mbbs","AFMC Pune","India","Pune, India","Elite Military Medicine","Free + Commitment","Physical excellence alongside elite surgical residency systems."),
        ("mbbs","Maulana Azad Medical College (MAMC), Delhi","India","Delhi, India","Top Clinical Caseload","₹15,000/Yr","Incredible clinical diversity; thousands of outpatients daily."),
        ("mbbs","King George's Medical University (KGMU), Lucknow","India","Lucknow, India","Top Legacy Medical","₹60,000/Yr","Centuries-old surgical excellence and clinical neural networks."),
        ("mbbs","Harvard Medical School","Abroad","Cambridge, USA","#1 Global Medical","$68,000/Yr","Frontier of surgical breakthroughs and computational biology."),
        ("mbbs","Johns Hopkins School of Medicine","Abroad","Baltimore, USA","#1 Clinical Research","$66,000/Yr","Global gold standard for neurosurgery and epidemiological models."),
        ("mbbs","University of Oxford (Medical Sciences)","Abroad","Oxford, UK","#1 UK Clinical Track","£48,000/Yr","Brilliant translational medicine and traditional tutor-led groups."),
        ("mbbs","Karolinska Institutet, Sweden","Abroad","Stockholm, Sweden","Nobel Prize Institution","Free–€20k/Yr","Awards Nobel Prize in Medicine; supreme research infrastructure."),
        ("mbbs","University of Toronto (Temerty Faculty)","Abroad","Toronto, Canada","#1 Canada Medical","$52,000/Yr","Unmatched stem-cell diagnostics and surgical robotics tech."),
        # ── B.PHARM ──────────────────────────────────────────────
        ("bpharm","Bombay College of Pharmacy, Mumbai","India","Mumbai, India","#1 Pharmacy Mumbai","₹80,000–1.2 Lakhs/Yr","Oldest and most prestigious pharmacy college in India."),
        ("bpharm","JSS College of Pharmacy, Ooty & Mysore","India","Mysore, India","Top South Pharmacy","₹1.0–1.5 Lakhs/Yr","Excellent research publications and pharma industry placements."),
        ("bpharm","Jamia Hamdard, New Delhi","India","Delhi, India","Top Unani & Pharmacy","₹1.0–1.5 Lakhs/Yr","Strong drug discovery research; herbal and classical pharmacy."),
        ("bpharm","NIPER (Natl. Institute of Pharmaceutical Education)","India","Mohali, India","#1 Research Pharmacy","₹80,000–1.0 Lakhs/Yr","Government institute producing India's top pharmaceutical scientists."),
        ("bpharm","Manipal College of Pharmaceutical Sciences","India","Manipal, India","Top Deemed Pharmacy","₹1.5–2.0 Lakhs/Yr","Strong clinical pharmacy and hospital pharmacy placements."),
        ("bpharm","UCL School of Pharmacy, London","Abroad","London, UK","#1 UK Pharmacy","£24,000/Yr","World-leading pharmaceutical sciences and drug discovery research."),
        ("bpharm","University of Michigan College of Pharmacy","Abroad","Ann Arbor, USA","#1 US Pharmacy","$50,000/Yr","Top accredited PharmD; excellent clinical and research pharmacy."),
        ("bpharm","Monash University Faculty of Pharmacy","Abroad","Melbourne, Australia","#1 Australia Pharmacy","$36,000/Yr","Exceptional clinical pharmacy and pharmaceutical sciences output."),
        ("bpharm","University of Toronto (Pharmacy)","Abroad","Toronto, Canada","#1 Canada Pharmacy","$42,000/Yr","Premier accredited PharmD; outstanding clinical training rotations."),
        ("bpharm","KU Leuven, Belgium","Abroad","Leuven, Belgium","#1 European Pharmacy","€1,200/Yr","Internationally ranked pharmaceutical sciences at low tuition."),
        # ── B.SC BIOTECHNOLOGY ───────────────────────────────────
        ("bsc_biotech","JNU School of Biotechnology, Delhi","India","Delhi, India","#1 Biotech Research India","₹5,000–10,000/Yr","Exceptional genomics, proteomics, and bioinformatics research."),
        ("bsc_biotech","IIT Delhi (Biochem Engg & Biotech)","India","Delhi, India","Top IIT Biotech","₹2.4 Lakhs/Yr","Interdisciplinary biotech with strong engineering applications."),
        ("bsc_biotech","Manipal Academy of Higher Education","India","Manipal, India","Top Private Biotech","₹2.0–3.0 Lakhs/Yr","Well-equipped biotech labs; strong pharma industry placements."),
        ("bsc_biotech","VIT Vellore (Biotechnology)","India","Vellore, India","Top Private Biotech Growth","₹1.8–2.5 Lakhs/Yr","Large biotech research park; good industry and research placements."),
        ("bsc_biotech","Amity University (Biotech)","India","Noida, India","Top Private Biotech Noida","₹2.0–3.0 Lakhs/Yr","Industry-linked biotech curriculum; strong pharma tie-ups."),
        ("bsc_biotech","MIT (Biological Engineering)","Abroad","Cambridge, USA","#1 Global Biotech","$64,000/Yr","Pioneering CRISPR, synthetic biology, and biomedical engineering."),
        ("bsc_biotech","Johns Hopkins (Biomed Engineering)","Abroad","Baltimore, USA","#1 Biomedical Engineering","$66,000/Yr","World leader in translational biomedical research and medicine."),
        ("bsc_biotech","Imperial College London (Biotech)","Abroad","London, UK","#1 UK Biotech","£35,000/Yr","Outstanding life sciences and pharmaceutical engineering research."),
        ("bsc_biotech","TU Munich (Biotechnology)","Abroad","Munich, Germany","#1 European Biotech","€1,500/Yr","Leading industrial biotech; strong links to European biopharma."),
        ("bsc_biotech","University of Melbourne (Biomed)","Abroad","Melbourne, Australia","#1 Australia Life Sciences","$38,000/Yr","Exceptional translational research and clinical biotech pathway."),
        # ── BPT (PHYSIOTHERAPY) ──────────────────────────────────
        ("bpt","CMC Vellore (Physiotherapy)","India","Vellore, India","#1 BPT India","₹50,000–80,000/Yr","Top rehabilitation centre; exceptional clinical training exposure."),
        ("bpt","Manipal College of Allied Health Sciences","India","Manipal, India","Top Private BPT","₹2.0–2.5 Lakhs/Yr","Large clinical setup; strong sports and neurological physio tracks."),
        ("bpt","Sri Ramachandra University, Chennai","India","Chennai, India","Top Medical University BPT","₹1.0–1.5 Lakhs/Yr","Excellent inter-disciplinary exposure; NABH-accredited hospitals."),
        ("bpt","AIIMS (Allied Health Sciences)","India","Delhi, India","Top AIIMS BPT","₹10,000–20,000/Yr","Access to India's top clinical caseload; excellent faculty mentorship."),
        ("bpt","DY Patil University, Pune (BPT)","India","Pune, India","Top West India BPT","₹1.5–2.0 Lakhs/Yr","Modern rehab labs; good sports physio placements."),
        ("bpt","University of Melbourne (Physiotherapy)","Abroad","Melbourne, Australia","#1 Global Physiotherapy","$38,000/Yr","Gold-standard physiotherapy programme globally; top APA accreditation."),
        ("bpt","King's College London (Physiotherapy)","Abroad","London, UK","#1 UK Physiotherapy","£24,000/Yr","Excellent NHS clinical exposure; outstanding research output."),
        ("bpt","University of Toronto (PT)","Abroad","Toronto, Canada","#1 Canada Physiotherapy","$42,000/Yr","Excellent CAOT-accredited programme; strong sports physio track."),
        ("bpt","University of Sydney (Physiotherapy)","Abroad","Sydney, Australia","Top Australia BPT","$36,000/Yr","Top-5 global physio programme; excellent clinical placements."),
        ("bpt","McMaster University, Canada","Abroad","Hamilton, Canada","Top Evidence-Based BPT","$40,000/Yr","Pioneered evidence-based physiotherapy practice globally."),

        # ══════════════════════════════════════════════════════════
        # ── WORLD COLLEGES DATABASE (general search) ─────────────
        # ══════════════════════════════════════════════════════════

        # ── INDIA — DELHI ─────────────────────────────────────────
        ("general","University of Delhi (DU)","India","Delhi, India","Top Central University","₹10,000–40,000/Yr","Premier research university with 90+ affiliated colleges across all disciplines."),
        ("general","Indian Institute of Technology Delhi (IIT-D)","India","Delhi, India","#2 Engineering India","₹2.4 Lakhs/Yr","Top-tier research, stellar alumni, and strong global placement record."),
        ("general","Jawaharlal Nehru University (JNU)","India","Delhi, India","#1 Social Sciences","₹1,000–5,000/Yr","India's foremost research university for humanities, sciences and social sciences."),
        ("general","AIIMS New Delhi","India","Delhi, India","#1 Medical India","₹1,700 TOTAL","Absolute pinnacle of Indian medical education and clinical training."),
        ("general","Indian Institute of Technology Delhi — MBA","India","Delhi, India","Top IIT MBA","₹10 Lakhs/Yr","Tech-focused management programme with extraordinary STEM alumni network."),
        ("general","Delhi Technological University (DTU)","India","Delhi, India","Top State Engineering","₹1.5–2.0 Lakhs/Yr","Strong placements in IT and core engineering; excellent research output."),
        ("general","Netaji Subhas University of Technology (NSUT)","India","Delhi, India","Top Delhi Engineering","₹1.2–1.8 Lakhs/Yr","Rising engineering institution with excellent CS and ECE placements."),
        ("general","Jamia Millia Islamia","India","Delhi, India","Top Central University","₹20,000–50,000/Yr","Strong engineering, arts, law and media programmes; vibrant campus culture."),
        ("general","Indraprastha Institute of Information Technology Delhi (IIIT-D)","India","Delhi, India","#1 Delhi CS Specialist","₹3.0 Lakhs/Yr","Pure CS research focus; excellent startup ecosystem and global placements."),
        ("general","Miranda House, DU","India","Delhi, India","#1 Women's College India","₹10,000–20,000/Yr","NAAC A++ accredited; consistently ranked India's top women's college."),
        ("general","Stephen's College, Delhi University","India","Delhi, India","Top Humanities DU","₹15,000–30,000/Yr","Elite English medium college; outstanding arts, sciences and philosophy faculty."),
        ("general","Ramjas College, DU","India","Delhi, India","Top Research DU","₹10,000–20,000/Yr","Strong research culture; excellent science, commerce and humanities departments."),
        ("general","Kamala Nehru College, DU","India","Delhi, India","Top Women's Arts DU","₹8,000–15,000/Yr","Excellent liberal arts environment with strong NCC and student activities."),
        ("general","Maulana Azad Medical College","India","Delhi, India","Top Clinical Medical","₹15,000/Yr","Incredible clinical diversity; attached to Lok Nayak Hospital."),

        # ── INDIA — MUMBAI ───────────────────────────────────────
        ("general","Indian Institute of Technology Bombay (IIT-B)","India","Mumbai, India","#1 National Engineering","₹2.5 Lakhs/Yr","Premier technology university; highest-paid placements in India."),
        ("general","Tata Institute of Social Sciences (TISS)","India","Mumbai, India","#1 Social Work India","₹80,000–1.5 Lakhs/Yr","World-class social sciences, HRM and development studies faculty."),
        ("general","University of Mumbai","India","Mumbai, India","Top Affiliating University","₹5,000–40,000/Yr","One of the largest universities globally; wide course range."),
        ("general","Institute of Chemical Technology (ICT Mumbai)","India","Mumbai, India","#1 Chemical Engineering","₹1.5–2.0 Lakhs/Yr","Best chemical technology institution in South Asia by global rankings."),
        ("general","KJ Somaiya College of Engineering","India","Mumbai, India","Top Private Engineering","₹1.8–2.5 Lakhs/Yr","Strong industry linkages; excellent CSE and mechanical programs."),
        ("general","Mithibai College of Arts","India","Mumbai, India","Top Mumbai Arts","₹15,000–25,000/Yr","Vibrant cultural hub; outstanding arts, commerce and science programmes."),
        ("general","Jai Hind College, Mumbai","India","Mumbai, India","Top Mumbai Commerce","₹20,000–40,000/Yr","Strong commerce and management faculty; excellent placement record."),
        ("general","Sophia College for Women","India","Mumbai, India","Top Women's Mumbai","₹30,000–50,000/Yr","Prestigious women's college; arts, science and commerce programs."),
        ("general","NMIMS University, Mumbai","India","Mumbai, India","Top Private University","₹3.0–5.0 Lakhs/Yr","Strong MBA, engineering, pharmacy and architecture programs."),

        # ── INDIA — BANGALORE ────────────────────────────────────
        ("general","Indian Institute of Science (IISc), Bangalore","India","Bangalore, India","#1 Research University India","₹30,000–50,000/Yr","Asia's top science and engineering research institution."),
        ("general","Indian Institute of Management Bangalore (IIM-B)","India","Bangalore, India","#1 MBA India","₹25 Lakhs/Yr","Top management school; best placements in Indian business education."),
        ("general","PES University, Bangalore","India","Bangalore, India","Top Private Engineering","₹2.5–3.5 Lakhs/Yr","Strong IT and engineering programs; excellent Bangalore tech placements."),
        ("general","RV College of Engineering, Bangalore","India","Bangalore, India","Top Autonomous Engineering","₹1.5–2.5 Lakhs/Yr","Excellent ECE and CSE programs; strong industry-academia collaboration."),
        ("general","MS Ramaiah Institute of Technology","India","Bangalore, India","Top Private Engineering","₹1.8–2.5 Lakhs/Yr","Strong engineering curriculum; good placements in core and IT sectors."),
        ("general","Jain University, Bangalore","India","Bangalore, India","Top Deemed University","₹2.0–3.0 Lakhs/Yr","Diverse programs across engineering, law, management and sciences."),
        ("general","Bangalore University","India","Bangalore, India","Top State University","₹5,000–20,000/Yr","Vast affiliated college network; diverse arts and science programs."),
        ("general","National Law School of India University (NLSIU)","India","Bangalore, India","#1 Law India","₹2.5–3.0 Lakhs/Yr","Premier law school; top placements in Supreme Court and law firms."),
        ("general","BMS College of Engineering","India","Bangalore, India","Top Autonomous College","₹1.5–2.0 Lakhs/Yr","One of Karnataka's oldest engineering colleges; excellent reputation."),

        # ── INDIA — CHENNAI ──────────────────────────────────────
        ("general","Indian Institute of Technology Madras (IIT-M)","India","Chennai, India","#1 NIRF Engineering","₹2.5 Lakhs/Yr","India's top-ranked engineering institution; world-class research park."),
        ("general","Anna University","India","Chennai, India","Top State University","₹50,000–80,000/Yr","Premier technology university in Tamil Nadu with strong industry linkages."),
        ("general","Loyola College, Chennai","India","Chennai, India","Top Autonomous Arts","₹40,000–60,000/Yr","Exceptional arts, commerce and science programs; strong alumni network."),
        ("general","Madras Christian College (MCC)","India","Chennai, India","Top Autonomous Science","₹30,000–50,000/Yr","Historic institution; excellent botany, zoology and chemistry departments."),
        ("general","SRM Institute of Science and Technology","India","Chennai, India","Top Private Engineering","₹1.8–2.5 Lakhs/Yr","Large campus; strong engineering and medical programs globally connected."),
        ("general","SASTRA University","India","Chennai, India","Top Deemed Engineering","₹1.2–1.8 Lakhs/Yr","Excellent academic rigour; strong placement record in IT sector."),
        ("general","Vellore Institute of Technology (VIT)","India","Vellore, India","#1 Private Engineering","₹1.8–2.5 Lakhs/Yr","Largest private engineering university; excellent international linkages."),
        ("general","Sri Ramachandra Institute of Higher Education","India","Chennai, India","Top Medical University","₹1.0–3.0 Lakhs/Yr","Comprehensive health sciences; NABH-accredited teaching hospitals."),

        # ── INDIA — HYDERABAD ────────────────────────────────────
        ("general","University of Hyderabad (UoH)","India","Hyderabad, India","#1 Humanities Research","₹5,000–15,000/Yr","Outstanding linguistics, sociology and social sciences research."),
        ("general","NALSAR University of Law, Hyderabad","India","Hyderabad, India","#2 Law India","₹2.0–2.5 Lakhs/Yr","Exceptional human rights, corporate and constitutional law programs."),
        ("general","Osmania University","India","Hyderabad, India","Top State University","₹5,000–20,000/Yr","Historic university; diverse programs in arts, sciences and engineering."),
        ("general","IIIT Hyderabad","India","Hyderabad, India","#1 CS Research India","₹2.5–3.0 Lakhs/Yr","Pure CS focus; extraordinary research output and top global offers."),
        ("general","International Institute of Information Technology (IIIT-H)","India","Hyderabad, India","Top Research IIIT","₹2.5 Lakhs/Yr","World-class AI, robotics and computational biology research."),

        # ── INDIA — KOLKATA ──────────────────────────────────────
        ("general","Jadavpur University","India","Kolkata, India","#1 Technical WB","₹5,000–15,000/Yr","Outstanding engineering, arts, and sciences; ranked among top 10 nationally."),
        ("general","Presidency University, Kolkata","India","Kolkata, India","Top Heritage University","₹5,000–10,000/Yr","Legendary institution; Nobel laureate alumni; brilliant research culture."),
        ("general","Calcutta University","India","Kolkata, India","Top Affiliating University","₹5,000–20,000/Yr","One of Asia's oldest universities; vast arts and science programs."),
        ("general","Indian Statistical Institute (ISI), Kolkata","India","Kolkata, India","#1 Stat & Math India","₹10,000–15,000/Yr","World-famous statistics and math faculty; pipeline to IES and academia."),
        ("general","St. Xavier's College, Kolkata","India","Kolkata, India","Top Autonomous Science","₹30,000–60,000/Yr","Excellent science, commerce and arts programs; strong cultural life."),
        ("general","Indian Institute of Technology Kharagpur (IIT-KGP)","India","Kharagpur, India","#1 Legacy IIT","₹2.3 Lakhs/Yr","Oldest and largest IIT; renowned across engineering disciplines."),

        # ── INDIA — PUNE ─────────────────────────────────────────
        ("general","Savitribai Phule Pune University","India","Pune, India","Top State University","₹5,000–20,000/Yr","Large affiliating university; strong science, law and management programs."),
        ("general","College of Engineering Pune (COEP)","India","Pune, India","Top Government Engineering","₹80,000–1.2 Lakhs/Yr","Maharashtra's oldest engineering college; strong technical placements."),
        ("general","Symbiosis International University","India","Pune, India","Top Private University","₹2.5–5.0 Lakhs/Yr","Diverse programs across law, business, engineering and media."),
        ("general","Fergusson College, Pune","India","Pune, India","Top Autonomous College","₹15,000–30,000/Yr","Prestigious arts and science college; strong research and alumni network."),
        ("general","Deccan College Post-Graduate Research Institute","India","Pune, India","Top Archaeology India","₹10,000–20,000/Yr","World-renowned archaeology and linguistics research institution."),

        # ── INDIA — AHMEDABAD ────────────────────────────────────
        ("general","Indian Institute of Management Ahmedabad (IIM-A)","India","Ahmedabad, India","#1 MBA Globally Ranked","₹24 Lakhs/Yr","India's most prestigious management school; legendary alumni network."),
        ("general","CEPT University","India","Ahmedabad, India","#1 Architecture India","₹2.0–3.0 Lakhs/Yr","Best architecture, urban planning and design institution in India."),
        ("general","National Institute of Design (NID)","India","Ahmedabad, India","#1 Design India","₹1.5–2.5 Lakhs/Yr","Premier design school; alumni lead global product and graphic design."),
        ("general","Gujarat University","India","Ahmedabad, India","Top State University","₹5,000–20,000/Yr","Vast affiliated college network; wide range of programs."),
        ("general","NIFT Ahmedabad","India","Ahmedabad, India","Top Fashion Design","₹1.5–2.0 Lakhs/Yr","Leading fashion technology institute; strong industry placement record."),

        # ── INDIA — OTHER CITIES ─────────────────────────────────
        ("general","Indian Institute of Technology Kanpur (IIT-K)","India","Kanpur, India","Top IIT Engineering","₹2.4 Lakhs/Yr","Exceptional aerospace, CSE and mechanical programs; excellent research."),
        ("general","Indian Institute of Technology Roorkee (IIT-R)","India","Roorkee, India","Top IIT Infrastructure","₹2.4 Lakhs/Yr","Oldest technical institute; excellent civil and geological engineering."),
        ("general","Indian Institute of Management Calcutta (IIM-C)","India","Kolkata, India","Top 3 IIM","₹27 Lakhs/Yr","Leading management school; strongest finance and consulting placements."),
        ("general","National Institute of Technology Trichy (NIT-T)","India","Trichy, India","#1 NIT India","₹1.5–2.0 Lakhs/Yr","Best NIT; strong placements and exceptional research output."),
        ("general","Manipal Academy of Higher Education","India","Manipal, India","Top Deemed University","₹2.0–3.5 Lakhs/Yr","Wide programs; engineering, medicine, management and communication."),
        ("general","Amrita Vishwa Vidyapeetham","India","Coimbatore, India","Top Multi-Disciplinary","₹2.0–3.0 Lakhs/Yr","Strong engineering and medicine programs; excellent research culture."),
        ("general","Banaras Hindu University (BHU)","India","Varanasi, India","Top Central University","₹5,000–20,000/Yr","One of India's largest universities; strong research and heritage."),
        ("general","Aligarh Muslim University (AMU)","India","Aligarh, India","Top Central University","₹5,000–20,000/Yr","Historic institution; excellent engineering, medicine and social sciences."),
        ("general","Panjab University, Chandigarh","India","Chandigarh, India","Top North India University","₹10,000–30,000/Yr","Leading university for law, sciences and management in North India."),
        ("general","PGIMER, Chandigarh","India","Chandigarh, India","Top Post-Graduate Medical","₹10,000–20,000/Yr","Premier post-graduate medical institute; world-class clinical training."),
        ("general","Banasthali Vidyapith","India","Jaipur, India","#1 Women's Tech University","₹1.5–2.5 Lakhs/Yr","Largest women's technical university; excellent STEM programs."),
        ("general","Malaviya National Institute of Technology (MNIT)","India","Jaipur, India","Top NIT Rajasthan","₹1.5–2.0 Lakhs/Yr","Strong placements in IT and core engineering sectors."),
        ("general","IIT Ropar","India","Rupnagar, India","Growing IIT Punjab","₹2.0 Lakhs/Yr","New-generation IIT; excellent research programs in emerging fields."),
        ("general","IIT Gandhinagar","India","Gandhinagar, India","Top Research IIT","₹2.0 Lakhs/Yr","Strong liberal arts plus engineering; design and cognitive science focus."),
        ("general","Tezpur University","India","Tezpur, India","Top Northeast India","₹10,000–20,000/Yr","Premier central university for northeast India; strong science programs."),
        ("general","North-Eastern Hill University (NEHU)","India","Shillong, India","Top Northeast University","₹5,000–15,000/Yr","Research university covering Northeast India's diverse academic needs."),

        # ══ UNITED STATES ════════════════════════════════════════
        ("general","Massachusetts Institute of Technology (MIT)","Abroad","Cambridge, USA","#1 World Engineering","$64,000/Yr","Definitive global centre of technological and scientific innovation."),
        ("general","Harvard University","Abroad","Cambridge, USA","#1 World University","$68,000/Yr","World's most prestigious university; alumni include 8 US Presidents."),
        ("general","Stanford University","Abroad","Stanford, USA","#1 Entrepreneurship","$66,000/Yr","Silicon Valley's academic engine; 40+ Nobel Laureates on faculty."),
        ("general","Yale University","Abroad","New Haven, USA","#1 Liberal Arts Ivy","$67,000/Yr","World-class law, drama and medicine; leading arts endowment globally."),
        ("general","Princeton University","Abroad","Princeton, USA","Top Ivy Research","$66,000/Yr","Exceptional undergraduate focus; groundbreaking STEM and humanities."),
        ("general","Columbia University","Abroad","New York, USA","Top Ivy NYC","$65,000/Yr","Prime New York location; excellent journalism, law and business."),
        ("general","University of Pennsylvania (UPenn)","Abroad","Philadelphia, USA","Top Ivy Applied","$65,000/Yr","Strong Wharton, Penn Medicine and nursing programs globally."),
        ("general","Cornell University","Abroad","Ithaca, USA","Top Ivy Practical","$64,000/Yr","Top hotel management, engineering, agriculture and law programs."),
        ("general","Dartmouth College","Abroad","Hanover, USA","Top Ivy Undergrad","$63,000/Yr","Intimate Ivy League experience; strong business Tuck alumni network."),
        ("general","Brown University","Abroad","Providence, USA","Top Ivy Open Curriculum","$65,000/Yr","Unique open curriculum; strong public health and humanities programs."),
        ("general","Johns Hopkins University","Abroad","Baltimore, USA","#1 Research Medical","$66,000/Yr","World leader in biomedical research and international studies."),
        ("general","Duke University","Abroad","Durham, USA","Top Research Private","$64,000/Yr","Excellent medicine, law and public policy; strong basketball culture."),
        ("general","Northwestern University","Abroad","Evanston, USA","Top Research Midwest","$63,000/Yr","Excellent journalism (Medill), law, business and engineering programs."),
        ("general","University of Chicago","Abroad","Chicago, USA","#1 Economic Theory","$65,000/Yr","Home of the Chicago School; 100+ Nobel Prize affiliations."),
        ("general","Vanderbilt University","Abroad","Nashville, USA","Top Research Southern","$62,000/Yr","Excellent medicine, education and law; vibrant Nashville campus."),
        ("general","Rice University","Abroad","Houston, USA","Top Research Compact","$60,000/Yr","Small but elite; excellent engineering, music and social sciences."),
        ("general","Washington University in St. Louis","Abroad","St. Louis, USA","Top Research Midwest","$62,000/Yr","Excellent medicine, social work and engineering programs."),
        ("general","Emory University","Abroad","Atlanta, USA","Top Research South","$61,000/Yr","Outstanding public health, law and theology programs."),
        ("general","Notre Dame University","Abroad","South Bend, USA","Top Catholic Research","$62,000/Yr","Excellent business, law and engineering with strong alumni network."),
        ("general","Georgetown University","Abroad","Washington DC, USA","Top Policy & Law","$61,000/Yr","Premier destination for diplomacy, law and international relations."),
        ("general","Carnegie Mellon University (CMU)","Abroad","Pittsburgh, USA","#1 CS & Robotics","$60,000/Yr","Global leader in computer science, AI and robotics research."),
        ("general","UC Los Angeles (UCLA)","Abroad","Los Angeles, USA","#1 Public US West","$48,000/Yr","World-class film, engineering and medicine in the heart of LA."),
        ("general","UC Berkeley","Abroad","Berkeley, USA","#1 Public Research US","$48,000/Yr","Pioneered internet, anti-war and open-source movements globally."),
        ("general","UC San Diego (UCSD)","Abroad","San Diego, USA","Top Public Research","$46,000/Yr","Excellence in oceanography, bioinformatics and computer science."),
        ("general","University of Michigan, Ann Arbor","Abroad","Ann Arbor, USA","#1 Public Midwest","$50,000/Yr","World-class engineering, business and medical programs."),
        ("general","University of Texas at Austin (UT Austin)","Abroad","Austin, USA","Top Public South","$40,000/Yr","Strong CS, business and engineering; massive Texas alumni network."),
        ("general","Georgia Institute of Technology","Abroad","Atlanta, USA","#1 Public Engineering East","$35,000/Yr","World-class industrial engineering, robotics and computing programs."),
        ("general","University of Washington, Seattle","Abroad","Seattle, USA","Top Public Pacific","$40,000/Yr","Excellent CS, medicine and oceanography; Amazon and Microsoft hub."),
        ("general","University of Illinois Urbana-Champaign","Abroad","Urbana, USA","Top Public Engineering","$38,000/Yr","Top-5 CS program; supercomputing and electrical engineering excellence."),
        ("general","New York University (NYU)","Abroad","New York, USA","#1 Urban Private","$63,000/Yr","Global campuses; excellent arts, law, business and social sciences."),
        ("general","Boston University","Abroad","Boston, USA","Top Research Urban","$60,000/Yr","Large urban research university; strong medicine, law and journalism."),
        ("general","Tufts University","Abroad","Medford, USA","Top Liberal Arts Research","$62,000/Yr","Excellent diplomacy, medicine and veterinary science programs."),
        ("general","Northeastern University","Abroad","Boston, USA","#1 Co-op Education","$60,000/Yr","Pioneering co-op work experience model; excellent global placements."),
        ("general","University of Southern California (USC)","Abroad","Los Angeles, USA","Top Private LA","$64,000/Yr","Excellent film, communications, engineering and business programs."),
        ("general","Caltech","Abroad","Pasadena, USA","#1 Science Compact","$60,000/Yr","Tiny but mighty; leads the world in physics, chemistry and space science."),
        ("general","Purdue University","Abroad","West Lafayette, USA","Top Engineering Public","$32,000/Yr","Strong aeronautical, mechanical and CS engineering programs."),
        ("general","Penn State University","Abroad","State College, USA","Top Land-Grant Public","$35,000/Yr","Excellent business, engineering and agriculture research programs."),
        ("general","Ohio State University","Abroad","Columbus, USA","Top Big Ten Public","$34,000/Yr","Large public research university with strong medicine and law programs."),
        ("general","Minnesota University","Abroad","Minneapolis, USA","Top Research Midwest","$34,000/Yr","Excellent medical school, business and engineering programs."),

        # ══ UNITED KINGDOM ════════════════════════════════════════
        ("general","University of Oxford","Abroad","Oxford, UK","#1 UK Global","£30,000/Yr","Oldest English-speaking university; unrivalled tutorial teaching system."),
        ("general","University of Cambridge","Abroad","Cambridge, UK","#2 UK Global","£30,000/Yr","Mathematical Tripos tradition; alumni include Newton, Darwin, Hawking."),
        ("general","Imperial College London","Abroad","London, UK","#1 UK STEM","£35,000/Yr","Dedicated science, engineering, medicine and business university."),
        ("general","University College London (UCL)","Abroad","London, UK","Top London Research","£28,000/Yr","Largest university in London; excellent engineering, law and sciences."),
        ("general","London School of Economics (LSE)","Abroad","London, UK","#1 Social Sciences UK","£28,000/Yr","Global hub for economics, politics, sociology and law research."),
        ("general","King's College London (KCL)","Abroad","London, UK","Top Central London","£27,000/Yr","Excellent medicine, law, dentistry and humanities programs."),
        ("general","University of Edinburgh","Abroad","Edinburgh, UK","Top Scottish Research","£26,000/Yr","Exceptional medicine, law, business and humanities programs."),
        ("general","University of Manchester","Abroad","Manchester, UK","Top Red Brick Research","£25,000/Yr","World-class physics, chemistry, business and social sciences."),
        ("general","University of Warwick","Abroad","Warwick, UK","Top Business & Science","£26,000/Yr","Excellent business, engineering, mathematics and social sciences."),
        ("general","University of Bristol","Abroad","Bristol, UK","Top Russell Group","£24,000/Yr","Strong aerospace, law, medicine and veterinary science programs."),
        ("general","Durham University","Abroad","Durham, UK","Top Collegiate UK","£24,000/Yr","Oxford-Cambridge style collegiate system; excellent law and theology."),
        ("general","University of Glasgow","Abroad","Glasgow, UK","Top Scottish Research","£24,000/Yr","Excellent medicine, engineering and social sciences programs."),
        ("general","Queen Mary University of London","Abroad","London, UK","Top London Research","£23,000/Yr","Strong medicine, law, engineering and humanities programs."),
        ("general","University of Sheffield","Abroad","Sheffield, UK","Top Russell Group","£22,000/Yr","Excellent engineering, architecture and social sciences programs."),
        ("general","University of Birmingham","Abroad","Birmingham, UK","Top Midlands Research","£22,000/Yr","Strong medicine, commerce and public policy programs."),
        ("general","University of Leeds","Abroad","Leeds, UK","Top Yorkshire Research","£22,000/Yr","Excellent textiles, law, dentistry and engineering programs."),
        ("general","University of Nottingham","Abroad","Nottingham, UK","Top Midlands University","£22,000/Yr","Strong pharmacy, engineering and business programs globally."),
        ("general","Southampton University","Abroad","Southampton, UK","Top Engineering UK","£22,000/Yr","World-leading ocean and earth sciences, electronics and aeronautics."),
        ("general","Cardiff University","Abroad","Cardiff, UK","Top Wales Research","£22,000/Yr","Strong journalism, engineering, law and medicine programs."),
        ("general","University of Bath","Abroad","Bath, UK","Top Enterprise UK","£22,000/Yr","Excellent management, engineering, pharmacy and architecture."),
        ("general","Heriot-Watt University","Abroad","Edinburgh, UK","Top Tech & Business","£18,000/Yr","Strong engineering, business and actuarial science; global Dubai campus."),
        ("general","Queen's University Belfast","Abroad","Belfast, UK","Top Northern Ireland","£20,000/Yr","Excellent medicine, law and engineering; Russell Group member."),
        ("general","London Business School","Abroad","London, UK","#1 European MBA","£48,000/Yr","Elite MBA; prime access to global finance and consulting recruiting."),

        # ══ CANADA ════════════════════════════════════════════════
        ("general","University of Toronto (UofT)","Abroad","Toronto, Canada","#1 Canada Research","$45,000/Yr","Canada's top university; world-class medicine, engineering and law."),
        ("general","University of British Columbia (UBC)","Abroad","Vancouver, Canada","#2 Canada Research","$40,000/Yr","Excellent forestry, Asian studies, commerce and engineering programs."),
        ("general","McGill University","Abroad","Montreal, Canada","#3 Canada Research","$42,000/Yr","Strong medicine, law and management; one of North America's oldest."),
        ("general","University of Waterloo","Abroad","Waterloo, Canada","#1 Canada Engineering","$38,000/Yr","Co-op engineering powerhouse; top-ranked CS and math programs."),
        ("general","McMaster University","Abroad","Hamilton, Canada","Top Canada Medical","$40,000/Yr","Problem-based learning pioneer; excellent medicine and engineering."),
        ("general","Western University","Abroad","London, Canada","Top Business Canada","$38,000/Yr","Excellent Ivey Business School; strong law and social sciences."),
        ("general","Queen's University","Abroad","Kingston, Canada","Top Canadian Arts","$42,000/Yr","Strong medicine, engineering and commerce with stunning campus."),
        ("general","University of Alberta","Abroad","Edmonton, Canada","Top Alberta Research","$35,000/Yr","World-class petroleum engineering, medicine and humanities."),
        ("general","University of Ottawa","Abroad","Ottawa, Canada","Top Bilingual Canada","$35,000/Yr","Excellent law, social sciences and medicine in Canada's capital."),
        ("general","Simon Fraser University (SFU)","Abroad","Vancouver, Canada","Top BC Research","$30,000/Yr","Strong CS, business and communication design programs."),

        # ══ AUSTRALIA ════════════════════════════════════════════
        ("general","University of Melbourne","Abroad","Melbourne, Australia","#1 Australia","$38,000/Yr","Australia's leading research university; Group of Eight member."),
        ("general","University of Sydney","Abroad","Sydney, Australia","#2 Australia","$40,000/Yr","Australia's first university; world-class law, medicine and engineering."),
        ("general","Australian National University (ANU)","Abroad","Canberra, Australia","#1 Australia Research","$38,000/Yr","National research university; excellent policy, STEM and humanities."),
        ("general","UNSW Sydney","Abroad","Sydney, Australia","Top Engineering AU","$40,000/Yr","World-class engineering, law and business; strong industry links."),
        ("general","University of Queensland (UQ)","Abroad","Brisbane, Australia","Top Queensland Research","$36,000/Yr","Excellent biological sciences, mining engineering and medicine."),
        ("general","Monash University","Abroad","Melbourne, Australia","Top Melbourne Research","$36,000/Yr","Large global university; excellent pharmacy, engineering and law."),
        ("general","University of Adelaide","Abroad","Adelaide, Australia","Top SA Research","$34,000/Yr","Group of Eight; excellent wine science, medicine and agriculture."),
        ("general","University of Western Australia (UWA)","Abroad","Perth, Australia","Top WA Research","$34,000/Yr","Strong mining, engineering, law and marine biology programs."),
        ("general","Macquarie University","Abroad","Sydney, Australia","Top Innovative Sydney","$35,000/Yr","Excellent actuarial science, linguistics and cognitive science."),
        ("general","Curtin University","Abroad","Perth, Australia","Top Tech Perth","$30,000/Yr","Excellent mining, engineering and business programs."),

        # ══ SINGAPORE ════════════════════════════════════════════
        ("general","National University of Singapore (NUS)","Abroad","Singapore","#1 Asia University","$22,000/Yr","Asia's top university; world-class law, engineering, business and medicine."),
        ("general","Nanyang Technological University (NTU)","Abroad","Singapore","Top Asia Tech","$22,000/Yr","World-class engineering, business and education; rapid research growth."),
        ("general","Singapore Management University (SMU)","Abroad","Singapore","#1 Singapore Business","$28,000/Yr","Premier business and law university; city campus in Singapore CBD."),

        # ══ GERMANY ══════════════════════════════════════════════
        ("general","Technical University of Munich (TUM)","Abroad","Munich, Germany","#1 Germany Engineering","€1,500/Yr","World-class engineering, life sciences and management at low tuition."),
        ("general","Ludwig Maximilian University Munich (LMU)","Abroad","Munich, Germany","Top Germany Research","€1,500/Yr","Excellent medicine, law, economics and natural sciences."),
        ("general","Heidelberg University","Abroad","Heidelberg, Germany","#1 Germany Life Sciences","€1,500/Yr","Germany's oldest university; world-class medicine and pharmacy."),
        ("general","RWTH Aachen University","Abroad","Aachen, Germany","Top Germany Engineering","€1,500/Yr","World-class mechanical, chemical and electrical engineering."),
        ("general","Humboldt University of Berlin","Abroad","Berlin, Germany","Top Berlin Arts","€1,500/Yr","Renowned for philosophy, social sciences and natural sciences."),
        ("general","Freie Universität Berlin","Abroad","Berlin, Germany","Top Berlin Social Sci","€1,500/Yr","Excellent social sciences, medicine and international affairs."),
        ("general","Technical University of Berlin (TU Berlin)","Abroad","Berlin, Germany","Top Berlin Engineering","€1,500/Yr","Strong engineering, architecture and urban planning programs."),
        ("general","Karlsruhe Institute of Technology (KIT)","Abroad","Karlsruhe, Germany","Top German Tech","€1,500/Yr","Excellent physics, engineering and computer science programs."),
        ("general","University of Stuttgart","Abroad","Stuttgart, Germany","Top Germany Automotive","€1,500/Yr","World-class aeronautics, automotive engineering and computer science."),
        ("general","University of Hamburg","Abroad","Hamburg, Germany","Top North Germany","€1,500/Yr","Excellent law, economics and marine sciences; in Europe's largest port city."),

        # ══ FRANCE ════════════════════════════════════════════════
        ("general","Sciences Po, Paris","Abroad","Paris, France","#1 Social Sciences EU","€15,000/Yr","Premier political science, international relations and journalism."),
        ("general","HEC Paris","Abroad","Paris, France","#1 European Business","€47,000/Yr","Europe's leading business school; top consulting and finance placements."),
        ("general","École Polytechnique (l'X)","Abroad","Paris, France","#1 France Engineering","€15,000/Yr","Elite grande école; world-class mathematics, physics and CS."),
        ("general","Sorbonne University (Paris IV)","Abroad","Paris, France","Top France Humanities","€3,000/Yr","Europe's oldest university; excellent arts, literature and science."),
        ("general","INSEAD","Abroad","Paris, France","#1 Global MBA","€90,000/Yr","World's most international business school; extraordinary alumni network."),
        ("general","École Normale Supérieure (ENS Paris)","Abroad","Paris, France","#1 Research French","€3,000/Yr","Produces most Fields Medal and Nobel Prize winners per capita."),
        ("general","ESSEC Business School","Abroad","Paris, France","Top French Grande École","€38,000/Yr","Excellent marketing, finance and luxury management programs."),

        # ══ NETHERLANDS ══════════════════════════════════════════
        ("general","TU Delft","Abroad","Delft, Netherlands","#1 Netherlands Engineering","€2,200/Yr","World-leading aerospace, civil and electrical engineering programs."),
        ("general","University of Amsterdam (UvA)","Abroad","Amsterdam, Netherlands","Top Netherlands Research","€2,200/Yr","Excellent business, law, social sciences and humanities programs."),
        ("general","Leiden University","Abroad","Leiden, Netherlands","Top Netherlands Heritage","€2,200/Yr","Netherlands' oldest university; world-class law, medicine and sciences."),
        ("general","Erasmus University Rotterdam","Abroad","Rotterdam, Netherlands","#1 Netherlands Business","€2,200/Yr","Erasmus School of Economics; world-class finance and business programs."),
        ("general","University of Groningen","Abroad","Groningen, Netherlands","Top Netherlands Sciences","€2,200/Yr","Strong physics, chemistry, medicine and technology programs."),

        # ══ SWITZERLAND ══════════════════════════════════════════
        ("general","ETH Zurich","Abroad","Zurich, Switzerland","#1 Continental Europe","CHF 1,500/Yr","Einstein's alma mater; world's top university for science and engineering."),
        ("general","EPFL (École Polytechnique Fédérale de Lausanne)","Abroad","Lausanne, Switzerland","#2 Continental Europe Tech","CHF 1,500/Yr","World-class engineering, computer science and life sciences."),
        ("general","University of Zurich","Abroad","Zurich, Switzerland","Top Swiss Research","CHF 1,500/Yr","Excellent medicine, economics, law and natural sciences."),
        ("general","Graduate Institute Geneva (IHEID)","Abroad","Geneva, Switzerland","#1 Global Policy","CHF 5,000/Yr","Integrated with UN; premier international relations and development."),
        ("general","IMD Business School, Lausanne","Abroad","Lausanne, Switzerland","#1 Exec MBA World","CHF 100,000/Yr","World's top executive MBA; extraordinary corporate leadership programs."),

        # ══ SWEDEN ════════════════════════════════════════════════
        ("general","Karolinska Institutet","Abroad","Stockholm, Sweden","#1 Medical Research Nordic","Free–€20k/Yr","Awards Nobel Prize in Medicine; global leader in biomedical research."),
        ("general","KTH Royal Institute of Technology","Abroad","Stockholm, Sweden","#1 Sweden Engineering","€15,000/Yr","Sweden's leading technical university; excellent engineering and CS."),
        ("general","Uppsala University","Abroad","Uppsala, Sweden","#1 Sweden Research","€15,000/Yr","Scandinavia's oldest university; strong medicine, law and sciences."),
        ("general","Lund University","Abroad","Lund, Sweden","Top Sweden Diversity","€15,000/Yr","Comprehensive university; strong engineering, medicine and social sciences."),
        ("general","Stockholm University","Abroad","Stockholm, Sweden","Top Stockholm Social Sci","€15,000/Yr","Excellent social sciences, natural sciences and humanities programs."),

        # ══ JAPAN ════════════════════════════════════════════════
        ("general","University of Tokyo (UTokyo)","Abroad","Tokyo, Japan","#1 Japan University","Free–¥535k/Yr","Japan's premier research university; excellent science, law and engineering."),
        ("general","Kyoto University","Abroad","Kyoto, Japan","#2 Japan Research","Free–¥535k/Yr","World-class natural sciences, engineering and humanities research."),
        ("general","Osaka University","Abroad","Osaka, Japan","Top Japan Medical","Free–¥535k/Yr","Excellent medicine, engineering and economics programs."),
        ("general","Tokyo Institute of Technology (Tokyo Tech)","Abroad","Tokyo, Japan","#1 Japan Engineering","Free–¥535k/Yr","Japan's top dedicated technology university; world-class STEM research."),
        ("general","Waseda University","Abroad","Tokyo, Japan","Top Japan Liberal Arts","¥1.4M/Yr","Japan's top private university; excellent business, law and social sciences."),
        ("general","Keio University","Abroad","Tokyo, Japan","Top Japan Private Research","¥1.4M/Yr","Leading private university; excellent medicine, economics and engineering."),
        ("general","Tohoku University","Abroad","Sendai, Japan","Top Japan Research Focus","Free–¥535k/Yr","World-class materials science and physics; excellent research output."),

        # ══ CHINA ════════════════════════════════════════════════
        ("general","Peking University (PKU)","Abroad","Beijing, China","#1 China University","$5,000/Yr","China's top comprehensive university; excellent humanities and sciences."),
        ("general","Tsinghua University","Abroad","Beijing, China","#1 China Engineering","$5,000/Yr","China's MIT; world-class engineering, CS and architecture programs."),
        ("general","Fudan University","Abroad","Shanghai, China","#1 China Social Sciences","$5,000/Yr","World-class medicine, economics and international studies programs."),
        ("general","Shanghai Jiao Tong University (SJTU)","Abroad","Shanghai, China","Top China Tech","$5,000/Yr","Excellent medicine, engineering and management programs."),
        ("general","Zhejiang University","Abroad","Hangzhou, China","Top China Comprehensive","$4,000/Yr","Strong CS, engineering, agriculture and medicine programs."),
        ("general","University of Science and Technology of China (USTC)","Abroad","Hefei, China","Top China Science","$4,000/Yr","World-class physics, chemistry and computer science programs."),

        # ══ SOUTH KOREA ══════════════════════════════════════════
        ("general","Seoul National University (SNU)","Abroad","Seoul, South Korea","#1 Korea University","$5,000/Yr","South Korea's top research university; world-class medicine and law."),
        ("general","KAIST (Korea Advanced Institute of Science and Technology)","Abroad","Daejeon, South Korea","#1 Korea Engineering","$5,000/Yr","Korea's leading science and technology university; outstanding CS."),
        ("general","Yonsei University","Abroad","Seoul, South Korea","Top Korea Private","$8,000/Yr","Excellent medicine, business, engineering and international studies."),
        ("general","Korea University","Abroad","Seoul, South Korea","Top Korea Research","$8,000/Yr","Strong law, business, medicine and engineering programs."),
        ("general","POSTECH","Abroad","Pohang, South Korea","#1 Korea Compact Tech","$5,000/Yr","World's best research output per capita; world-class materials science."),

        # ══ HONG KONG ════════════════════════════════════════════
        ("general","University of Hong Kong (HKU)","Abroad","Hong Kong","#1 Hong Kong","$18,000/Yr","Asia's global city university; excellent law, medicine and business."),
        ("general","HKUST","Abroad","Hong Kong","Top HK Engineering & Business","$18,000/Yr","World-class business and engineering; Silicon Valley of Asia gateway."),
        ("general","Chinese University of Hong Kong (CUHK)","Abroad","Hong Kong","Top HK Research","$17,000/Yr","Strong medicine, business and social sciences; bilingual campus."),

        # ══ UNITED ARAB EMIRATES ═════════════════════════════════
        ("general","NYU Abu Dhabi","Abroad","Abu Dhabi, UAE","#1 UAE Liberal Arts","$55,000/Yr","Free for most students; world-class liberal arts in the Gulf."),
        ("general","Khalifa University","Abroad","Abu Dhabi, UAE","#1 UAE Engineering","$12,000/Yr","Excellent aerospace, nuclear and petroleum engineering programs."),
        ("general","University of Sharjah","Abroad","Sharjah, UAE","Top UAE Comprehensive","$8,000/Yr","Wide program range; strong engineering, architecture and medicine."),
        ("general","Heriot-Watt University Dubai","Abroad","Dubai, UAE","Top Dubai Engineering","$18,000/Yr","Scottish university in Dubai; strong engineering and business programs."),
        ("general","Murdoch University Dubai","Abroad","Dubai, UAE","Top Dubai Law & IT","$12,000/Yr","Australian university in Dubai; strong business, IT and law programs."),
        ("general","American University in Dubai (AUD)","Abroad","Dubai, UAE","Top US-Style Dubai","$20,000/Yr","American-style education; strong engineering, business and arts."),

        # ══ IRELAND ══════════════════════════════════════════════
        ("general","Trinity College Dublin (TCD)","Abroad","Dublin, Ireland","#1 Ireland Research","€20,000/Yr","Ireland's most prestigious; world-class law, medicine and sciences."),
        ("general","University College Dublin (UCD)","Abroad","Dublin, Ireland","Top Ireland Research","€18,000/Yr","Ireland's largest university; excellent business, law and engineering."),
        ("general","University College Cork (UCC)","Abroad","Cork, Ireland","Top Ireland Sciences","€16,000/Yr","Strong food science, medicine and environmental sciences programs."),
        ("general","Dublin City University (DCU)","Abroad","Dublin, Ireland","Top Ireland Innovation","€16,000/Yr","Excellent communications, computing and business programs."),

        # ══ NEW ZEALAND ══════════════════════════════════════════
        ("general","University of Auckland","Abroad","Auckland, New Zealand","#1 New Zealand","$35,000/Yr","NZ's largest and leading research university; excellent engineering."),
        ("general","University of Otago","Abroad","Dunedin, New Zealand","Top NZ Medicine","$32,000/Yr","Best dental and medical school in New Zealand; strong research culture."),
        ("general","Victoria University of Wellington","Abroad","Wellington, New Zealand","Top NZ Policy","$32,000/Yr","Excellent law, public policy and creative arts programs."),

        # ══ SOUTH AFRICA ═════════════════════════════════════════
        ("general","University of Cape Town (UCT)","Abroad","Cape Town, South Africa","#1 Africa University","$8,000/Yr","Africa's top research university; excellent medicine, law and business."),
        ("general","University of the Witwatersrand (Wits)","Abroad","Johannesburg, South Africa","Top SA Engineering","$6,000/Yr","Excellent mining, engineering, medicine and arts programs."),

        # ══ ISRAEL ════════════════════════════════════════════════
        ("general","Technion – Israel Institute of Technology","Abroad","Haifa, Israel","#1 Israel Engineering","$10,000/Yr","World-class CS, engineering and aerospace; Israel's MIT."),
        ("general","Hebrew University of Jerusalem","Abroad","Jerusalem, Israel","#1 Israel Research","$10,000/Yr","Outstanding agriculture, medicine, law and humanities programs."),
        ("general","Tel Aviv University","Abroad","Tel Aviv, Israel","Top Israel Research","$10,000/Yr","Excellent business, law, engineering and social sciences programs."),

        # ══ MALAYSIA / SOUTHEAST ASIA ════════════════════════════
        ("general","University of Malaya (UM)","Abroad","Kuala Lumpur, Malaysia","#1 Malaysia","$5,000/Yr","Malaysia's oldest and top research university; excellent medicine."),
        ("general","Monash University Malaysia","Abroad","Kuala Lumpur, Malaysia","Top Intl Malaysia","$12,000/Yr","Australian university in Malaysia; strong business and engineering."),
        ("general","Chulalongkorn University","Abroad","Bangkok, Thailand","#1 Thailand","$5,000/Yr","Thailand's top university; excellent medicine, engineering and business."),
        ("general","Asian Institute of Technology (AIT)","Abroad","Bangkok, Thailand","Top SE Asia Tech","$10,000/Yr","Excellent engineering and environmental management programs."),
        ("general","University of the Philippines (UP Manila)","Abroad","Manila, Philippines","#1 Philippines","$3,000/Yr","Philippines' national research university; strong medicine and law."),
        ("general","Institut Teknologi Bandung (ITB)","Abroad","Bandung, Indonesia","#1 Indonesia Engineering","$3,000/Yr","Indonesia's premier technical institution; world-class engineering."),
        ("general","Universitas Indonesia (UI)","Abroad","Jakarta, Indonesia","#1 Indonesia","$3,000/Yr","Indonesia's largest research university; strong medicine and law."),

        # ══ BRAZIL / LATIN AMERICA ════════════════════════════════
        ("general","Universidade de São Paulo (USP)","Abroad","São Paulo, Brazil","#1 Latin America","$2,000/Yr","Latin America's largest and best university; wide academic range."),
        ("general","Universidad de Buenos Aires (UBA)","Abroad","Buenos Aires, Argentina","Top Argentina Research","Free","World-class medicine, law and social sciences at zero tuition."),
        ("general","Pontificia Universidad Católica de Chile (PUC)","Abroad","Santiago, Chile","#1 Chile","$8,000/Yr","Chile's top private university; excellent business, engineering and law."),

        # ══ MIDDLE EAST & UAE ═════════════════════════════════════
        ("general","American University of Beirut (AUB)","Abroad","Beirut, Lebanon","#1 Middle East Liberal Arts","$22,000/Yr","Premier regional liberal arts university; strong medicine, engineering and business."),
        ("general","King Abdullah University of Science and Technology (KAUST)","Abroad","Thuwal, Saudi Arabia","#1 Saudi Arabia Research","Free+Stipend","World-class research in AI, materials, and energy; fully funded graduate program."),
        ("general","American University of Sharjah (AUS)","Abroad","Sharjah, UAE","Top UAE Engineering","$18,000/Yr","US-accredited university in UAE; excellent architecture, engineering and business."),
        ("general","University of Dubai","Abroad","Dubai, UAE","Top Dubai Business","$14,000/Yr","Strong MBA, accounting and information systems in the global business hub."),
        ("general","Khalifa University","Abroad","Abu Dhabi, UAE","#1 UAE STEM","$12,000/Yr","World-class aerospace, nuclear energy and AI research in Abu Dhabi."),

        # ══ NORDIC COUNTRIES ═════════════════════════════════════
        ("general","KTH Royal Institute of Technology","Abroad","Stockholm, Sweden","#1 Nordic Engineering","€3,000/Yr","Sweden's top technical university; excellent CS, robotics and sustainability research."),
        ("general","Lund University","Abroad","Lund, Sweden","Top Sweden Research","€3,000/Yr","Comprehensive research university; strong medicine, law and engineering."),
        ("general","University of Copenhagen","Abroad","Copenhagen, Denmark","#1 Denmark Research","€3,000/Yr","Excellent pharmaceutical, life sciences and social sciences research."),
        ("general","Technical University of Denmark (DTU)","Abroad","Copenhagen, Denmark","#1 Denmark Engineering","€3,000/Yr","Outstanding sustainable technology, wind energy and pharma engineering."),
        ("general","Aalto University","Abroad","Helsinki, Finland","#1 Finland Engineering","€3,000/Yr","Strong design, technology and business programs; excellent Nordic innovation."),
        ("general","University of Helsinki","Abroad","Helsinki, Finland","Top Finland Research","€3,000/Yr","Excellent medicine, biosciences and humanities programs."),
        ("general","University of Oslo","Abroad","Oslo, Norway","#1 Norway Research","€3,000/Yr","Strong law, humanities and petroleum engineering programs."),
        ("general","Norwegian University of Science and Technology (NTNU)","Abroad","Trondheim, Norway","Top Norway Engineering","€3,000/Yr","World-class marine technology, renewable energy and computer science."),

        # ══ OTHER EUROPE ═════════════════════════════════════════
        ("general","École Normale Supérieure (ENS), Paris","Abroad","Paris, France","#1 France Elite Grande École","Free–€400/Yr","France's most selective institution; alumni include 15 Fields Medalists and 13 Nobel Laureates."),
        ("general","École Polytechnique (X), Paris","Abroad","Palaiseau, France","#1 France Engineering Grande École","€15,000/Yr","Military engineering grande école; world-class mathematics, physics and CS."),
        ("general","Delft University of Technology (TU Delft)","Abroad","Delft, Netherlands","#1 Netherlands Engineering","€2,200/Yr","World-class aerospace, architecture and water management engineering."),
        ("general","University of Amsterdam","Abroad","Amsterdam, Netherlands","Top Netherlands Social Sciences","€2,200/Yr","Strong economics, law, social sciences and life sciences programs."),
        ("general","Leiden University","Abroad","Leiden, Netherlands","Top Netherlands Research","€2,200/Yr","Netherlands' oldest university; excellent law, medicine and area studies."),
        ("general","University of Zurich","Abroad","Zurich, Switzerland","Top Switzerland Research","$3,000/Yr","Excellent medicine, law, economics and natural sciences programs."),
        ("general","EPFL (École Polytechnique Fédérale de Lausanne)","Abroad","Lausanne, Switzerland","#1 Switzerland Tech","$3,000/Yr","World-class engineering, life sciences and digital humanities research."),
        ("general","Ghent University","Abroad","Ghent, Belgium","Top Belgium Research","€4,000/Yr","Strong pharmacy, veterinary science, engineering and social sciences."),
        ("general","KU Leuven","Abroad","Leuven, Belgium","#1 Belgium Research","€4,000/Yr","Belgium's top university; excellent medicine, law, theology and engineering."),
        ("general","Trinity College Dublin","Abroad","Dublin, Ireland","#1 Ireland Research","€23,000/Yr","Ireland's most prestigious university; excellent law, medicine and business."),
        ("general","University College Dublin (UCD)","Abroad","Dublin, Ireland","Top Ireland University","€22,000/Yr","Strong business, engineering and veterinary medicine programs."),
        ("general","Bocconi University","Abroad","Milan, Italy","#1 Italy Business","€15,000/Yr","Europe's premier business school; excellent finance, law and management."),
        ("general","University of Bologna","Abroad","Bologna, Italy","World's Oldest University","€4,000/Yr","Historic institution; strong law, humanities, medicine and natural sciences."),
        ("general","Complutense University of Madrid","Abroad","Madrid, Spain","#1 Spain Research","€2,500/Yr","Spain's largest university; broad programs in law, medicine and social sciences."),
        ("general","University of Barcelona","Abroad","Barcelona, Spain","Top Spain Research","€3,000/Yr","Excellent biosciences, economics and humanities programs in a vibrant city."),

        # ══ NEW ZEALAND ══════════════════════════════════════════
        ("general","University of Auckland","Abroad","Auckland, New Zealand","#1 New Zealand","$32,000/Yr","New Zealand's top research university; strong engineering, law and medicine."),
        ("general","Victoria University of Wellington","Abroad","Wellington, New Zealand","Top NZ Law & Policy","$30,000/Yr","Excellent law, business, and creative arts programs in the capital."),

        # ══ INDIA — NEW ADDITIONS ════════════════════════════════
        ("general","IIT Guwahati","India","Guwahati, India","Top Northeast IIT","₹2.0 Lakhs/Yr","Excellent design, CS and engineering programs; strong northeast India research hub."),
        ("general","IIT Jodhpur","India","Jodhpur, India","Growing IIT Rajasthan","₹2.0 Lakhs/Yr","New-generation IIT; strong AI and sustainable technology research."),
        ("general","IIT Indore","India","Indore, India","Top Central India IIT","₹2.0 Lakhs/Yr","Excellent physics, CS and electrical engineering programs."),
        ("general","IIT Mandi","India","Mandi, India","Top IIT Himachal Pradesh","₹2.0 Lakhs/Yr","Strong CS, electrical and engineering programs in the Himalayas."),
        ("general","IIT Tirupati","India","Tirupati, India","Growing IIT Andhra","₹2.0 Lakhs/Yr","New-generation IIT with strong engineering and research focus."),
        ("general","Ashoka University","India","Sonipat, India","#1 Liberal Arts India","₹15–18 Lakhs/Yr","India's leading liberal arts university; interdisciplinary programs with global faculty."),
        ("general","Azim Premji University","India","Bangalore, India","Top Social Sciences India","₹1–3 Lakhs/Yr","Excellent education, development studies and humanities programs."),
        ("general","OP Jindal Global University","India","Sonipat, India","Top Private Law & IR","₹8–15 Lakhs/Yr","Excellent law, international relations, business and journalism programs."),
        ("general","Flame University, Pune","India","Pune, India","Top Liberal Arts Private","₹10–14 Lakhs/Yr","US-style liberal arts education; strong humanities, business and communication."),
        ("general","Shiv Nadar University","India","Greater Noida, India","Top Private Research","₹3–5 Lakhs/Yr","Strong engineering, natural sciences and liberal arts programs."),
        ("general","Plaksha University","India","Mohali, India","New-Gen Tech University","₹5–7 Lakhs/Yr","Problem-first tech education; incubation-first approach and strong global connections."),
        ("general","NIFT Delhi (National Institute of Fashion Technology)","India","Delhi, India","#1 Fashion India","₹1.8–2.5 Lakhs/Yr","Premier fashion institute; alumni lead global fashion and apparel brands."),
        ("general","NID Ahmedabad (National Institute of Design)","India","Ahmedabad, India","#1 Design India","₹1.5–2.5 Lakhs/Yr","India's premier design institution; alumni define global product and visual design."),
        ("general","Pearl Academy, Delhi","India","Delhi, India","Top Private Design","₹3–4.5 Lakhs/Yr","Leading design, fashion and media arts institution; strong industry connections."),
        ("general","Srishti Manipal Institute of Art, Design and Technology","India","Bangalore, India","Top Design Research India","₹3–4 Lakhs/Yr","Interdisciplinary design and arts school; outstanding faculty and research culture."),
        ("general","School of Planning and Architecture (SPA), Delhi","India","Delhi, India","#1 Architecture India","₹20,000–50,000/Yr","Premier architecture and planning school; alumni define India's built environment."),
        ("general","CEPT University, Ahmedabad","India","Ahmedabad, India","#2 Architecture India","₹2–3 Lakhs/Yr","Outstanding architecture, urban design and construction management programs."),
        ("general","Sir JJ College of Architecture, Mumbai","India","Mumbai, India","Top Mumbai Architecture","₹50,000–80,000/Yr","Historic institution with a modernist legacy; strong studio culture and alumni network."),
        ("general","Homi Bhabha National Institute (HBNI)","India","Mumbai, India","Top Nuclear Sciences","₹10,000–30,000/Yr","Research university of India's nuclear program; world-class science programs."),
        ("general","Tata Institute of Fundamental Research (TIFR)","India","Mumbai, India","#1 India Fundamental Research","₹10,000–20,000/Yr","India's top fundamental sciences institution; world-class mathematics and physics."),
        ("general","Indian Institute of Science (IISc), Bangalore","India","Bangalore, India","#1 India Research University","₹30,000–60,000/Yr","India's top-ranked research university; exceptional science and engineering research."),

        # ── Design & Creative Arts — SCHOOL ──────────────────────
        ("school_design","Sir J.J. School of Art, Mumbai","India","Mumbai, India","#1 Fine Arts School India","₹20,000–40,000/Yr","India's oldest art school; exceptional foundation for design and fine arts entry."),
        ("school_design","DPS R.K. Puram (Arts & Media)","India","Delhi, India","Top CBSE Arts School","₹2–3 Lakhs/Yr","Strong fine arts and media program; solid foundation for NID and NIFT prep."),
        ("school_design","Scindia School, Gwalior","India","Gwalior, India","Top Boarding School Arts","₹8–10 Lakhs/Yr","Rich creative culture; excellent fine arts and architecture foundation program."),
        ("school_design","The Heritage School, Kolkata","India","Kolkata, India","Top Creative Day School","₹2–3 Lakhs/Yr","Strong arts and design orientation with excellent extracurricular programs."),
        ("school_design","Pune International School","India","Pune, India","Top IB Arts School","₹4–6 Lakhs/Yr","IB curriculum with strong visual arts and design extended essay opportunities."),
        ("school_design","BRIT School for Performing Arts","Abroad","London, UK","#1 UK Creative Arts School","Free (State-Funded)","Produced Adele, Amy Winehouse; best performing and creative arts school globally."),
        ("school_design","LaGuardia Arts High School","Abroad","New York, USA","#1 US Arts School","Free (Merit)","NYC's premier arts high school for visual art, drama, dance, music, and design."),
        ("school_design","Pratt High School Program","Abroad","New York, USA","Top US Design Foundation","$55,000/Yr","Early design studio exposure; direct pathway and preference to Pratt Institute."),
        ("school_design","Vancouver School of Arts and Academics","Abroad","Vancouver, Canada","Top Canada Arts School","Free (Public)","Strong visual arts, digital media and design foundation programs."),
        ("school_design","Bauhaus-Schule, Dessau","Abroad","Berlin, Germany","Top Design Foundation School","€5,000/Yr","Legendary Bauhaus heritage; excellent design philosophy and foundation arts."),

        # ── Design — Product & Industrial ────────────────────────
        ("bdes_product","National Institute of Design (NID), Ahmedabad","India","Ahmedabad, India","#1 Industrial Design India","₹1.5–2.5 Lakhs/Yr","Premier design institution; alumni lead global product and experience design."),
        ("bdes_product","IIT Bombay (IDC School of Design)","India","Mumbai, India","#1 Academic Design India","₹2.5 Lakhs/Yr","Industrial Design Centre; IIT-level rigour applied to design research."),
        ("bdes_product","IIT Delhi (Design Programme)","India","Delhi, India","Top IIT Design","₹2.4 Lakhs/Yr","Strong product and experience design programs; excellent research culture."),
        ("bdes_product","MITID Pune","India","Pune, India","Top Private Industrial Design","₹2.0–2.5 Lakhs/Yr","Excellent industrial design faculty; strong auto sector industry linkages."),
        ("bdes_product","Srishti Manipal Institute, Bangalore","India","Bangalore, India","Top Design Research","₹3.0–4.0 Lakhs/Yr","Interdisciplinary design school; strong research and international exposure."),
        ("bdes_product","Rhode Island School of Design (RISD)","Abroad","Providence, USA","#1 US Industrial Design","$56,000/Yr","World's most prestigious design school; alumni at Apple, Nike, IDEO, and Google."),
        ("bdes_product","Royal College of Art (RCA), London","Abroad","London, UK","#1 Global Art & Design","£26,000/Yr","World's #1 art and design university; alumni define global design culture."),
        ("bdes_product","Eindhoven University of Technology (TU/e)","Abroad","Eindhoven, Netherlands","#1 European Industrial Design","€2,200/Yr","Home to Philips Design; leading sustainable and systems design research."),
        ("bdes_product","Art Center College of Design, Pasadena","Abroad","Pasadena, USA","#1 US Transportation Design","$53,000/Yr","Premier for automotive and product design; clients include BMW and Apple."),
        ("bdes_product","Politecnico di Milano (Product Design)","Abroad","Milan, Italy","#1 European Design School","€4,000/Yr","Heart of Italian design culture; Ferrari, Alessi, and Armani connections."),

        # ── Design — Communication & Graphic ─────────────────────
        ("bdes_comm","NID Ahmedabad (Communication Design)","India","Ahmedabad, India","#1 Graphic Design India","₹1.5–2.5 Lakhs/Yr","Renowned communication design; alumni lead global branding studios."),
        ("bdes_comm","Pearl Academy Delhi/Mumbai","India","Delhi/Mumbai, India","Top Private Comm Design","₹3.0–4.0 Lakhs/Yr","Strong communication design and media arts; excellent industry connections."),
        ("bdes_comm","Symbiosis Institute of Design, Pune","India","Pune, India","Top Private Comm Design","₹2.0–3.0 Lakhs/Yr","Excellent branding and digital media design; strong placement record."),
        ("bdes_comm","Srishti Manipal, Bangalore","India","Bangalore, India","Top Interdisciplinary Design","₹3.0–4.0 Lakhs/Yr","Research-led communication design with technology integration."),
        ("bdes_comm","IIT Guwahati (Design)","India","Guwahati, India","Top Northeast IIT Design","₹2.0 Lakhs/Yr","Strong visual communication and interaction design programs."),
        ("bdes_comm","Parsons School of Design, New York","Abroad","New York, USA","#1 US Graphic Design","$56,000/Yr","NYC icon; alumni at Donna Karan, Tom Ford, Marc Jacobs, and global agencies."),
        ("bdes_comm","Central Saint Martins (UAL), London","Abroad","London, UK","#1 UK Arts & Design","£25,000/Yr","Alexander McQueen and Stella McCartney alumni; world's most creative campus."),
        ("bdes_comm","SVA (School of Visual Arts), NYC","Abroad","New York, USA","Top NYC Visual Arts","$47,000/Yr","Premier BFA graphic arts; deep advertising and publishing industry links."),
        ("bdes_comm","Hyper Island, Stockholm","Abroad","Stockholm, Sweden","Top Digital Creative School","€12,000/Yr","Industry-embedded creative technology and digital design program."),
        ("bdes_comm","HfG Offenbach School of Design","Abroad","Frankfurt, Germany","Top German Visual Communication","€1,500/Yr","Strong Bauhaus heritage; rigorous visual communication and typography training."),

        # ── Design — Fashion ──────────────────────────────────────
        ("bdes_fashion","NIFT Delhi","India","Delhi, India","#1 Fashion India","₹1.8–2.5 Lakhs/Yr","Premier fashion institute; alumni at Manish Malhotra, BIBA, and global brands."),
        ("bdes_fashion","NIFT Mumbai","India","Mumbai, India","#1 West India Fashion","₹1.8–2.5 Lakhs/Yr","Strong Bollywood and retail fashion connections; excellent placements."),
        ("bdes_fashion","NID Gandhinagar (Textile & Apparel)","India","Gandhinagar, India","Top NID Fashion","₹1.5–2.5 Lakhs/Yr","Textile and fashion design with craft heritage integration."),
        ("bdes_fashion","Pearl Academy Delhi","India","Delhi, India","Top Private Fashion","₹3.0–4.5 Lakhs/Yr","Strong luxury fashion, styling and retail management programs."),
        ("bdes_fashion","Symbiosis Institute of Design, Pune","India","Pune, India","Top Fashion Design Private","₹2.5–3.5 Lakhs/Yr","Excellent fashion and lifestyle design program; strong industry links."),
        ("bdes_fashion","Central Saint Martins (UAL), London","Abroad","London, UK","#1 Fashion Globally","£25,000/Yr","Most storied fashion school on earth; alumni define haute couture globally."),
        ("bdes_fashion","Parsons School of Design, New York","Abroad","New York, USA","#1 US Fashion School","$56,000/Yr","Top runway-to-retail school; alumni include Donna Karan and Tom Ford."),
        ("bdes_fashion","Fashion Institute of Technology (FIT), NYC","Abroad","New York, USA","Top Fashion Business","$25,000/Yr","Excellent fashion business, marketing and design programs in NYC."),
        ("bdes_fashion","IFM Paris (Institut Français de la Mode)","Abroad","Paris, France","#1 French Fashion","€18,000/Yr","Heart of Paris couture culture; LVMH, Dior, and Chanel recruitment pipeline."),
        ("bdes_fashion","ESMOD Paris","Abroad","Paris, France","Top French Fashion School","€18,500/Yr","Classic French fashion design and modélisme education."),

        # ── Architecture ─────────────────────────────────────────
        ("barch","School of Planning and Architecture (SPA), Delhi","India","Delhi, India","#1 Architecture India","₹20,000–50,000/Yr","Premier architecture school; alumni designed iconic Indian infrastructure."),
        ("barch","CEPT University, Ahmedabad","India","Ahmedabad, India","#2 Architecture India","₹2.0–3.0 Lakhs/Yr","Outstanding architecture and urban design; strong research ecosystem."),
        ("barch","IIT Roorkee (Architecture)","India","Roorkee, India","#3 Architecture India","₹2.4 Lakhs/Yr","Strong technical and design fusion; excellent placements in AEC industry."),
        ("barch","Chandigarh College of Architecture","India","Chandigarh, India","Top Government Architecture","₹80,000–1.2 Lakhs/Yr","Famous for Le Corbusier's city influence; strong modernist architecture training."),
        ("barch","Sir JJ College of Architecture, Mumbai","India","Mumbai, India","Top Mumbai Architecture","₹50,000–80,000/Yr","Historic institution with strong modernist legacy and studio culture."),
        ("barch","ETH Zurich (Architecture)","Abroad","Zurich, Switzerland","#1 World Architecture","$3,000/Yr","The definitive architecture school; Peter Zumthor and Rem Koolhaas connections."),
        ("barch","Architectural Association (AA), London","Abroad","London, UK","#1 UK Architecture","£26,000/Yr","Most avant-garde architecture school globally; alumni include Zaha Hadid."),
        ("barch","Harvard Graduate School of Design","Abroad","Cambridge, USA","#1 US Architecture","$68,000/Yr","Elite architecture, urban planning and landscape design programs."),
        ("barch","Politecnico di Milano (Architecture)","Abroad","Milan, Italy","#1 Italian Architecture","€4,000/Yr","World-class architecture in the design capital of Europe."),
        ("barch","TU Delft (Architecture)","Abroad","Delft, Netherlands","Top European Architecture","€2,200/Yr","Largest architecture faculty in the Netherlands; strong sustainability focus."),

        # ── UX / Interaction Design ───────────────────────────────
        ("bdes_ux","IIT Bombay (IDC — Interaction Design)","India","Mumbai, India","#1 UX Design India","₹2.5 Lakhs/Yr","Premier human-computer interaction and UX research in India."),
        ("bdes_ux","IIT Guwahati (Design)","India","Guwahati, India","Top IIT Interaction Design","₹2.0 Lakhs/Yr","Strong UX and interaction design; excellent faculty-to-student ratio."),
        ("bdes_ux","Srishti Manipal, Bangalore","India","Bangalore, India","Top Interaction Design","₹3.0–4.0 Lakhs/Yr","Interdisciplinary UX and service design; strong tech-design integration."),
        ("bdes_ux","NID Bangalore (Interaction Design)","India","Bangalore, India","Top NID UX","₹1.5–2.5 Lakhs/Yr","NID's dedicated interaction design centre; strong tech ecosystem proximity."),
        ("bdes_ux","MITID Pune (Interaction Design)","India","Pune, India","Top Private UX","₹2.0–2.5 Lakhs/Yr","Excellent HCI and digital product design curriculum."),
        ("bdes_ux","Carnegie Mellon University (HCI Institute)","Abroad","Pittsburgh, USA","#1 HCI Globally","$60,000/Yr","Birthplace of HCI as a discipline; Google, Apple, and IBM recruit directly here."),
        ("bdes_ux","Copenhagen Institute of Interaction Design (CIID)","Abroad","Copenhagen, Denmark","#1 European Interaction Design","€18,000/Yr","Globally respected interaction design intensive; strong alumni in Big Tech."),
        ("bdes_ux","RCA (Interaction Design)","Abroad","London, UK","Top UK Interaction Design","£26,000/Yr","Cutting-edge service and systems design; strong alumni in global tech companies."),
        ("bdes_ux","Aalto University (Collaborative Design)","Abroad","Helsinki, Finland","Top Nordic Design","€3,000/Yr","Strong user-centred design and Nordic simplicity philosophy."),
        ("bdes_ux","Pratt Institute (Communication Design)","Abroad","New York, USA","Top US UX/Interactive","$55,000/Yr","Excellent graphic and interactive design programs in Brooklyn, NYC."),

        # ── Animation & Game Design ───────────────────────────────
        ("bdes_animation","NID Ahmedabad (Film & Video Communication)","India","Ahmedabad, India","#1 Animation Design India","₹1.5–2.5 Lakhs/Yr","Prestigious animation and film design; alumni in Pixar and top Indian studios."),
        ("bdes_animation","Whistling Woods International, Mumbai","India","Mumbai, India","Top Film & Media India","₹4.0–6.0 Lakhs/Yr","India's premier film school; excellent VFX and animation programs."),
        ("bdes_animation","Arena Animation, Mumbai","India","Mumbai, India","Top Animation Training","₹1.0–1.5 Lakhs/Yr","Practical-first animation; excellent VFX and game art training."),
        ("bdes_animation","Srishti Manipal (Film & Animation)","India","Bangalore, India","Top Design-Led Animation","₹3.0–4.0 Lakhs/Yr","Excellent experimental animation and digital arts curriculum."),
        ("bdes_animation","Manipal Institute of Communication","India","Manipal, India","Top Media & Animation","₹2.5–3.5 Lakhs/Yr","Strong animation and digital media program; good industry connections."),
        ("bdes_animation","California Institute of the Arts (CalArts)","Abroad","Valencia, USA","#1 Animation Globally","$58,000/Yr","Disney's school; virtually every major Pixar and Disney film traces alumni here."),
        ("bdes_animation","Ringling College of Art and Design","Abroad","Sarasota, USA","#1 US Computer Animation","$48,000/Yr","Outstanding 3D animation and game design; strong Pixar placement record."),
        ("bdes_animation","School of Visual Arts (SVA), NYC","Abroad","New York, USA","Top NYC Animation","$47,000/Yr","Excellent MFA animation and graphic narrative programs in NYC."),
        ("bdes_animation","Gobelins, Paris","Abroad","Paris, France","#1 European Animation","€15,000/Yr","World-renowned animation school; alumni at Europe's and Hollywood's top studios."),
        ("bdes_animation","Vancouver Film School","Abroad","Vancouver, Canada","Top Canada Film & Game","$36,000/Yr","Intensive film and game design training; strong industry placement record."),
    ]

    c.executemany(
        "INSERT INTO colleges (course_key,name,region,location,rank,fees,features) VALUES (?,?,?,?,?,?,?)",
        colleges
    )

    careers = [
        # ── College — Commerce & Management — INDIA ───────────────
        ("College Student","Commerce & Management","India","Investment Banking Analyst","₹18–28 LPA","High","Executing M&A valuations, IPO structuring, and equity capital market deals at top Indian banks."),
        ("College Student","Commerce & Management","India","Management Consultant (Big-4)","₹12–22 LPA","High","Redesigning operations for India's largest conglomerates across FMCG, banking, and infrastructure."),
        ("College Student","Commerce & Management","India","Chartered Accountant (CA)","₹8–18 LPA","Steady","Leading statutory audits, tax planning, and financial reporting for major Indian corporates."),
        ("College Student","Commerce & Management","India","FinTech Product Manager","₹15–30 LPA","Exponential","Building UPI-native payment products, lending algorithms, and neobank platforms at Razorpay, Zepto, or Groww."),
        ("College Student","Commerce & Management","India","Equity Research Analyst","₹10–20 LPA","High","Publishing sector deep-dives and stock models for Indian fund houses and brokerage firms."),
        # ── College — Commerce & Management — ABROAD ─────────────
        ("College Student","Commerce & Management","Abroad","Investment Banker (Wall Street / London)","$120k–$180k","High","Executing billion-dollar leveraged buyouts, cross-border mergers, and global debt syndications."),
        ("College Student","Commerce & Management","Abroad","Private Equity Associate","$150k–$250k","High","Sourcing mid-market buyouts across the US and European tech and consumer sectors."),
        ("College Student","Commerce & Management","Abroad","Hedge Fund Quant Analyst","$160k–$350k","Exponential","Designing systematic macro strategies and high-frequency arbitrage models at global funds."),
        ("College Student","Commerce & Management","Abroad","Global M&A Director","$200k–$400k","High","Negotiating cross-border corporate acquisitions and multi-billion asset disposals in London or New York."),
        ("College Student","Commerce & Management","Abroad","Treasury & Risk Manager (MNC)","$110k–$160k","Steady","Controlling FX exposure, liquidity pools, and interest rate risk across multi-currency balance sheets."),
        # ── College — Engineering & Technology — INDIA ────────────
        ("College Student","Engineering & Technology","India","AI / ML Engineer","₹22–45 LPA","Exponential","Building production-grade deep learning pipelines, LLM integrations, and recommendation engines at Flipkart, Swiggy, or ISRO."),
        ("College Student","Engineering & Technology","India","Software Development Engineer (SDE)","₹15–38 LPA","High","Designing scalable microservices and distributed systems at product companies like Zepto, PhonePe, or Juspay."),
        ("College Student","Engineering & Technology","India","DevOps & Cloud Architect","₹18–40 LPA","High","Engineering multi-cloud infrastructure, Kubernetes clusters, and zero-downtime CI/CD pipelines for large-scale Indian startups."),
        ("College Student","Engineering & Technology","India","Data Scientist","₹14–32 LPA","High","Driving pricing models, churn prediction, and fraud detection systems at Paytm, Ola, or CRED."),
        ("College Student","Engineering & Technology","India","Cybersecurity Analyst","₹12–25 LPA","High","Hardening enterprise security postures and running red-team operations for banks and defence PSUs."),
        # ── College — Engineering & Technology — ABROAD ───────────
        ("College Student","Engineering & Technology","Abroad","AI Research Scientist (FAANG)","$160k–$350k","Exponential","Publishing frontier deep learning and LLM research at Google DeepMind, OpenAI, or Meta FAIR."),
        ("College Student","Engineering & Technology","Abroad","Distributed Systems Engineer","$140k–$260k","High","Building globally distributed databases and real-time streaming systems at Netflix, Stripe, or Cloudflare."),
        ("College Student","Engineering & Technology","Abroad","Quantitative Developer","$180k–$450k","Exponential","Translating high-frequency trading strategies into ultra-low-latency C++ execution engines at Citadel or Two Sigma."),
        ("College Student","Engineering & Technology","Abroad","Robotics & Autonomous Systems Engineer","$130k–$230k","High","Developing perception stacks, SLAM algorithms, and motion planners for autonomous vehicles at Waymo or Boston Dynamics."),
        ("College Student","Engineering & Technology","Abroad","Cybersecurity Principal Engineer","$150k–$280k","High","Architecting zero-trust networks and leading incident response at CrowdStrike, Palo Alto, or Microsoft Security."),
        # ── College — Humanities & Social Sciences — INDIA ────────
        ("College Student","Humanities & Social Sciences","India","Indian Foreign Service (IFS) Officer","₹8–15 LPA (Govt)","Steady","Representing India at bilateral negotiations, treaty drafting, and consular operations worldwide post-UPSC."),
        ("College Student","Humanities & Social Sciences","India","Policy Analyst (Think Tank / Govt)","₹8–18 LPA","High","Shaping national education, climate, or trade policy at ORF, NITI Aayog, or state planning bodies."),
        ("College Student","Humanities & Social Sciences","India","Corporate Legal Associate","₹10–22 LPA","High","Advising top Indian companies on M&A, SEBI compliance, and commercial contracts at AZB or Cyril Amarchand."),
        ("College Student","Humanities & Social Sciences","India","Corporate Communications Lead","₹12–24 LPA","High","Directing PR strategy, crisis communications, and media relations for major Indian brands and conglomerates."),
        ("College Student","Humanities & Social Sciences","India","Investigative Journalist","₹6–15 LPA","Steady","Uncovering political and corporate wrongdoing for The Wire, The Hindu, or NDTV in print, broadcast, or digital."),
        # ── College — Humanities & Social Sciences — ABROAD ──────
        ("College Student","Humanities & Social Sciences","Abroad","UN Policy Advisor (Geneva / New York)","$90k–$140k","Steady","Drafting global human rights frameworks and sustainable development policy instruments for UN agencies."),
        ("College Student","Humanities & Social Sciences","Abroad","International Arbitration Attorney","$150k–$280k","High","Litigating multi-billion disputes between states and corporations at ICC or ICSID in London or Paris."),
        ("College Student","Humanities & Social Sciences","Abroad","Geopolitical Risk Consultant","$110k–$190k","High","Advising Fortune 500 companies on conflict zones, sanctions, and political risk at Eurasia Group or Control Risks."),
        ("College Student","Humanities & Social Sciences","Abroad","Foreign Correspondent (Global Media)","$80k–$140k","Steady","Reporting live from conflict zones and global summits for Reuters, BBC World, or The New York Times."),
        ("College Student","Humanities & Social Sciences","Abroad","Global Think-Tank Director","$130k–$220k","High","Leading international security, economics, or climate research at Brookings, Chatham House, or RAND Corporation."),
        # ── College — Medicine & Life Sciences — INDIA ────────────
        ("College Student","Medicine & Life Sciences","India","Cardiothoracic Surgeon","₹35–65 LPA","High","Performing coronary artery bypass, valve replacements, and complex congenital heart surgeries at AIIMS or Apollo."),
        ("College Student","Medicine & Life Sciences","India","Clinical Oncologist","₹25–50 LPA","High","Designing targeted chemotherapy, immunotherapy, and precision radiation regimens at Tata Memorial or HCG."),
        ("College Student","Medicine & Life Sciences","India","Interventional Radiologist","₹20–42 LPA","High","Executing image-guided minimally invasive procedures across vascular and neuro disciplines."),
        ("College Student","Medicine & Life Sciences","India","Biomedical Researcher (ICMR / DBT)","₹10–22 LPA","Exponential","Conducting government-funded clinical trials and genomics research at national institutes."),
        ("College Student","Medicine & Life Sciences","India","Neurologist / Neurosurgeon","₹30–65 LPA","High","Treating epilepsy, stroke, and brain tumours with advanced surgical and pharmacological protocols."),
        # ── College — Medicine & Life Sciences — ABROAD ───────────
        ("College Student","Medicine & Life Sciences","Abroad","Interventional Neurosurgeon (US / UK)","$500k–$800k","Exponential","Operating on cerebral aneurysms, AVM resections, and spinal cord tumours at Johns Hopkins or Oxford."),
        ("College Student","Medicine & Life Sciences","Abroad","Cardiothoracic Surgeon (International)","$400k–$700k","High","Executing robotic-assisted cardiac surgery and heart transplant programmes at Mayo Clinic or Cleveland Clinic."),
        ("College Student","Medicine & Life Sciences","Abroad","Clinical Oncologist (US / Canada)","$320k–$550k","High","Leading immunotherapy trials and precision oncology programmes at Memorial Sloan Kettering or MD Anderson."),
        ("College Student","Medicine & Life Sciences","Abroad","Biomedical Gene Therapist","$160k–$280k","Exponential","Developing CRISPR-based therapies for rare diseases at Broad Institute, Novartis, or Regeneron."),
        ("College Student","Medicine & Life Sciences","Abroad","Epidemiology Director (WHO / CDC)","$140k–$220k","High","Modelling global outbreak dynamics and directing public health emergency responses for international agencies."),
        # ── School — Commerce & Management ───────────────────────
        ("School Student","Commerce & Management","Both","Financial Portfolio Advisor","₹8–15 LPA","High","Managing wealth metrics and preparing investment data maps."),
        ("School Student","Commerce & Management","Both","Corporate Accountant Trainee","₹6–10 LPA","Steady","Assisting corporate managers in calculating balance sheet metrics."),
        ("School Student","Commerce & Management","Both","Taxation Analyst","₹7–12 LPA","Steady","Processing corporate tax filings and analysing regulatory exemptions."),
        ("School Student","Commerce & Management","Both","Stock Market Equity Associate","₹10–18 LPA","Exponential","Tracking public equity markets and compiling stock behaviour trackers."),
        ("School Student","Commerce & Management","Both","E-Commerce Business Strategist","₹9–16 LPA","High","Analysing user behaviour to increase digital inventory sales."),
        # ── School — Engineering & Technology ────────────────────
        ("School Student","Engineering & Technology","Both","Junior Python / Systems Developer","₹6–12 LPA","High","Writing structural script wrappers and functional system blocks."),
        ("School Student","Engineering & Technology","Both","QA Software Automation Tester","₹6–10 LPA","High","Testing build instances for algorithmic exceptions and network faults."),
        ("School Student","Engineering & Technology","Both","Cybersecurity Operations Analyst","₹8–14 LPA","High","Monitoring threat logs for pattern anomalies across structural systems."),
        ("School Student","Engineering & Technology","Both","Data Analytics Junior Specialist","₹8–15 LPA","Exponential","Compiling messy data into clean dashboard visualisation engines."),
        ("School Student","Engineering & Technology","Both","Embedded Systems Prototyper","₹7–13 LPA","High","Programming microcontrollers and writing hardware-level sensor controls."),
        # ── School — Humanities & Social Sciences ────────────────
        ("School Student","Humanities & Social Sciences","Both","NGO Public Policy Coordinator","₹5–8 LPA","Steady","Structuring community development plans and deployment files."),
        ("School Student","Humanities & Social Sciences","Both","Media Communications Journalist","₹6–12 LPA","Steady","Investigating policy issues and compiling investigative reports."),
        ("School Student","Humanities & Social Sciences","Both","Public Relations Liaison","₹7–13 LPA","High","Constructing strategic messaging profiles to mitigate operational risks."),
        ("School Student","Humanities & Social Sciences","Both","Political Campaign Data Specialist","₹8–15 LPA","High","Analysing regional voting profiles to build demographic outreach systems."),
        ("School Student","Humanities & Social Sciences","Both","Digital Content Creator","₹5–11 LPA","Exponential","Managing public cultural documentation and content networks."),
        # ── School — Medicine & Life Sciences ────────────────────
        ("School Student","Medicine & Life Sciences","Both","Clinical Research Assistant","₹6–10 LPA","High","Tracking patient metrics for pharmaceutical development pipelines."),
        ("School Student","Medicine & Life Sciences","Both","Pharmaceutical Regulatory Consultant","₹7–12 LPA","High","Reviewing drug safety dossiers for chemical compliance standards."),
        ("School Student","Medicine & Life Sciences","Both","Bio-Medical Instrumentation Technician","₹6–11 LPA","Steady","Calibrating MRI systems, ventilators and hospital equipment nodes."),
        ("School Student","Medicine & Life Sciences","Both","Genetic Counselling Associate","₹8–13 LPA","Exponential","Analysing chromosomal history to report inheritance risk factors."),
        ("School Student","Medicine & Life Sciences","Both","Dietetics & Nutrition Consultant","₹6–10 LPA","High","Constructing clinical physiological diet plans for diagnostic recovery."),

        # ── College — Engineering & Technology — INDIA (extra) ────
        ("College Student","Engineering & Technology","India","AI/ML Engineer","₹18–40 LPA","Exponential","Building large-scale ML models, LLM fine-tuning pipelines and AI product features at India's top unicorns."),
        ("College Student","Engineering & Technology","India","Cloud Solutions Architect","₹20–45 LPA","Exponential","Designing multi-cloud infrastructure for Indian enterprises migrating from on-prem to AWS/Azure/GCP."),
        ("College Student","Engineering & Technology","India","Robotics & Automation Engineer","₹12–25 LPA","High","Programming industrial robots, cobots and AGVs for India's fast-growing automotive and logistics sectors."),
        ("College Student","Engineering & Technology","India","DevOps / SRE Engineer","₹15–30 LPA","Exponential","Building CI/CD pipelines, Kubernetes clusters and zero-downtime deployments for SaaS platforms."),
        ("College Student","Engineering & Technology","India","Semiconductor Design Engineer","₹18–35 LPA","High","Designing VLSI circuits and SoC architectures for India Semiconductor Mission fab units."),
        ("College Student","Engineering & Technology","India","Renewable Energy Engineer","₹10–20 LPA","High","Designing solar, wind and green-hydrogen systems for India's 500 GW renewable target by 2030."),
        # ── College — Engineering & Technology — ABROAD (extra) ──
        ("College Student","Engineering & Technology","Abroad","Machine Learning Research Scientist","$180k–$400k","Exponential","Publishing frontier AI/ML research at OpenAI, DeepMind, Google Brain and Meta FAIR."),
        ("College Student","Engineering & Technology","Abroad","Autonomous Systems Engineer","$160k–$280k","Exponential","Developing self-driving perception stacks and motion planning algorithms at Waymo or Tesla."),
        ("College Student","Engineering & Technology","Abroad","Quantum Computing Engineer","$150k–$300k","Exponential","Designing error-corrected qubits and quantum algorithms at IBM, Google Quantum AI, or IonQ."),
        ("College Student","Engineering & Technology","Abroad","Cybersecurity Architect","$150k–$250k","Exponential","Designing enterprise zero-trust architectures and threat intelligence systems globally."),
        ("College Student","Engineering & Technology","Abroad","Space Systems Engineer","$120k–$200k","High","Designing satellite constellations, propulsion systems and mission control for SpaceX or NASA."),

        # ── College — Humanities & Social Sciences — INDIA (extra) ─
        ("College Student","Humanities & Social Sciences","India","IAS / IPS Officer (Civil Services)","₹12–18 LPA","Steady","Administering districts, formulating policy and managing public services as India's premier civil servant."),
        ("College Student","Humanities & Social Sciences","India","Political Campaign Strategist","₹10–25 LPA","High","Running data-driven electoral campaigns for national parties leveraging psephology and social media."),
        ("College Student","Humanities & Social Sciences","India","NGO Program Director","₹8–15 LPA","Steady","Leading social impact programs in education, health and women's empowerment across rural India."),
        ("College Student","Humanities & Social Sciences","India","UX Researcher","₹10–22 LPA","Exponential","Conducting ethnographic and behavioural research to inform product design at India's top tech companies."),
        ("College Student","Humanities & Social Sciences","India","Investigative Journalist","₹8–18 LPA","Steady","Breaking high-impact stories on politics, business and society for digital-first Indian newsrooms."),
        # ── College — Humanities & Social Sciences — ABROAD (extra)─
        ("College Student","Humanities & Social Sciences","Abroad","Behavioural Economist","$120k–$200k","High","Designing nudge-based policy interventions for governments and international organisations."),
        ("College Student","Humanities & Social Sciences","Abroad","International Development Consultant","$80k–$140k","Steady","Managing multilateral aid programs at the World Bank, UNDP or USAID across 50+ countries."),
        ("College Student","Humanities & Social Sciences","Abroad","Literary Agent","$60k–$120k","Steady","Representing authors in New York and London, negotiating deals with Penguin, HarperCollins and Macmillan."),
        ("College Student","Humanities & Social Sciences","Abroad","Human Rights Lawyer (International)","$100k–$180k","Steady","Arguing landmark cases before the ICC, ICJ and ECHR on behalf of persecuted individuals."),

        # ── College — Medicine & Life Sciences — INDIA (extra) ────
        ("College Student","Medicine & Life Sciences","India","Neurosurgeon","₹25–80 LPA","High","Performing complex intracranial and spinal surgeries at AIIMS, Medanta or Apollo networks."),
        ("College Student","Medicine & Life Sciences","India","Oncologist","₹20–60 LPA","High","Treating cancer patients with chemotherapy, immunotherapy and precision oncology at top Indian hospitals."),
        ("College Student","Medicine & Life Sciences","India","Genomics Data Scientist","₹15–30 LPA","Exponential","Analysing whole-genome sequencing data to identify disease biomarkers for Indian pharma companies."),
        ("College Student","Medicine & Life Sciences","India","Regulatory Affairs Specialist (Pharma)","₹10–20 LPA","High","Preparing CDSCO drug approval dossiers for generics and biosimilars exports."),
        ("College Student","Medicine & Life Sciences","India","Hospital Administrator","₹12–25 LPA","Steady","Managing operations, staffing and compliance for multi-specialty hospitals across India."),
        # ── College — Medicine & Life Sciences — ABROAD (extra) ──
        ("College Student","Medicine & Life Sciences","Abroad","Cardiothoracic Surgeon","$400k–$700k","High","Performing open-heart and thoracic procedures at Mayo Clinic, Cleveland Clinic or NHS hospitals."),
        ("College Student","Medicine & Life Sciences","Abroad","Clinical Trials Director","$150k–$250k","High","Managing Phase II–IV drug trials across multiple sites for Pfizer, Roche or J&J."),
        ("College Student","Medicine & Life Sciences","Abroad","Biotech Entrepreneur","$Variable","Exponential","Founding mRNA, CRISPR or synthetic biology ventures backed by Andreessen Horowitz or Flagship Pioneering."),

        # ── College — Commerce & Management — INDIA (extra) ──────
        ("College Student","Commerce & Management","India","Startup Founder / Entrepreneur","₹Variable","Exponential","Building India's next unicorn leveraging UPI-scale distribution and Bharat consumer insights."),
        ("College Student","Commerce & Management","India","Actuarial Analyst","₹12–22 LPA","High","Modelling insurance risk and pricing for LIC, HDFC Life and other Indian insurers."),
        ("College Student","Commerce & Management","India","GST & Tax Consultant","₹8–16 LPA","Steady","Advising corporates on GST compliance, transfer pricing and corporate tax structuring."),
        ("College Student","Commerce & Management","India","FMCG Brand Manager","₹12–22 LPA","High","Building P&G, HUL or ITC brand strategy, consumer promotions and new product pipelines."),
        # ── College — Commerce & Management — ABROAD (extra) ─────
        ("College Student","Commerce & Management","Abroad","Venture Capital Associate","$150k–$250k","Exponential","Sourcing early-stage AI, climate-tech and consumer deals for Sequoia, A16Z or Accel."),
        ("College Student","Commerce & Management","Abroad","Management Consultant (MBB)","$150k–$250k","High","Advising Fortune 500 boards on strategy, transformation and M&A at McKinsey, BCG or Bain."),
        ("College Student","Commerce & Management","Abroad","ESG Portfolio Manager","$130k–$220k","Exponential","Constructing sustainable investment portfolios aligned to Paris Agreement for global asset managers."),

        # ── College — Design & Creative Arts — INDIA ─────────────
        ("College Student","Design & Creative Arts","India","Product / Industrial Designer","₹8–20 LPA","High","Designing consumer electronics, furniture and lifestyle products for India's booming D2C brands."),
        ("College Student","Design & Creative Arts","India","UX / UI Designer","₹10–25 LPA","Exponential","Crafting intuitive mobile and web experiences for Razorpay, Meesho, Swiggy and India's unicorn startup ecosystem."),
        ("College Student","Design & Creative Arts","India","Fashion Designer","₹6–18 LPA","High","Creating original collections for Sabyasachi, Manish Malhotra, or launching a DTC fashion label."),
        ("College Student","Design & Creative Arts","India","Architect","₹8–20 LPA","High","Designing residential complexes, metro stations and mixed-use urban developments across India's tier-2 cities."),
        ("College Student","Design & Creative Arts","India","Brand Identity Designer","₹8–20 LPA","High","Building visual brand systems for India's new-age startups across logo, typography and motion design."),
        ("College Student","Design & Creative Arts","India","VFX / 3D Animation Artist","₹7–18 LPA","Exponential","Creating visual effects and CGI for Bollywood blockbusters and OTT platforms like Netflix India and Disney+ Hotstar."),
        ("College Student","Design & Creative Arts","India","Textile & Surface Designer","₹6–14 LPA","Steady","Developing surface patterns, weave structures and prints for India's handloom and export apparel industry."),
        ("College Student","Design & Creative Arts","India","Interior Designer","₹7–18 LPA","High","Designing premium residential, hospitality and commercial interiors for India's luxury real estate market."),
        ("College Student","Design & Creative Arts","India","Game Designer","₹8–22 LPA","Exponential","Building game worlds, mechanics and narrative systems for mobile-first Indian gaming studios."),
        ("College Student","Design & Creative Arts","India","Design Researcher","₹8–18 LPA","High","Conducting ethnographic studies to inform product and service design at India's design consultancies."),
        # ── College — Design & Creative Arts — ABROAD ────────────
        ("College Student","Design & Creative Arts","Abroad","Industrial / Product Designer","$80k–$180k","High","Designing iconic hardware products at Apple, Dyson, Nike or IDEO's global innovation studios."),
        ("College Student","Design & Creative Arts","Abroad","Senior UX Designer","$120k–$220k","Exponential","Leading end-to-end experience design for Google, Figma, Airbnb or Meta's billion-user platforms."),
        ("College Student","Design & Creative Arts","Abroad","Luxury Fashion Designer","$60k–$200k","High","Creating haute couture and RTW collections at Dior, Chanel, Louis Vuitton or Gucci in Paris or Milan."),
        ("College Student","Design & Creative Arts","Abroad","Principal Architect","$120k–$250k","High","Designing award-winning museums, towers and public spaces at Zaha Hadid, BIG or Foster+Partners."),
        ("College Student","Design & Creative Arts","Abroad","Creative Director (Advertising)","$120k–$250k","High","Directing brand campaigns for Fortune 500 companies at Wieden+Kennedy, BBDO or Ogilvy globally."),
        ("College Student","Design & Creative Arts","Abroad","Lead Animator / VFX Supervisor","$100k–$200k","High","Directing character animation and visual effects at Pixar, Disney, ILM or Weta Digital."),
        ("College Student","Design & Creative Arts","Abroad","Design Director (Tech Product)","$180k–$350k","Exponential","Leading design culture and product vision for Figma, Stripe, Linear or Notion globally."),
        ("College Student","Design & Creative Arts","Abroad","Jewellery Designer","$60k–$150k","Steady","Creating fine jewellery collections for Tiffany, Cartier, Bulgari or launching an independent label."),
        ("College Student","Design & Creative Arts","Abroad","Game Art Director","$100k–$180k","Exponential","Setting visual language and art direction for AAA titles at Ubisoft, EA, Naughty Dog or Riot Games."),
        ("College Student","Design & Creative Arts","Abroad","Photographer / Cinematographer","$60k–$200k","Steady","Shooting major editorial, commercial campaigns and feature films for global publications and studios."),

        # ── School — Design & Creative Arts ──────────────────────
        ("School Student","Design & Creative Arts","Both","Graphic Design Intern","₹3–6 LPA","Exponential","Creating visual assets, social media creatives and brand collateral for digital-first companies."),
        ("School Student","Design & Creative Arts","Both","Art Direction Assistant","₹4–8 LPA","High","Supporting senior creative directors on advertising shoots, layouts and brand guidelines."),
        ("School Student","Design & Creative Arts","Both","Textile & Craft Artist","₹4–9 LPA","Steady","Designing handloom patterns, block print motifs and surface illustrations for artisan craft labels."),
        ("School Student","Design & Creative Arts","Both","Photography Assistant","₹4–8 LPA","Steady","Supporting fashion and commercial photographers on set; building a portfolio for editorial work."),
        ("School Student","Design & Creative Arts","Both","Junior UI/UX Designer","₹5–10 LPA","Exponential","Wireframing and prototyping digital interfaces using Figma for app and web products."),
        ("School Student","Design & Creative Arts","Both","Animation Trainee","₹4–8 LPA","Exponential","Creating 2D character animations and motion graphics for short-form content and branded media."),
        ("School Student","Design & Creative Arts","Both","Set & Production Design Assistant","₹5–10 LPA","High","Supporting set decoration and production design on film and advertising shoots."),

        # ── School — Engineering & Technology (extra) ─────────────
        ("School Student","Engineering & Technology","Both","App Developer (Freelance)","₹3–8 LPA","Exponential","Building mobile apps and games independently or on Fiverr/Upwork while in school."),
        ("School Student","Engineering & Technology","Both","AI Prompt Engineer","₹4–10 LPA","Exponential","Crafting structured prompts and fine-tuning LLM outputs for startups and content platforms."),
        ("School Student","Engineering & Technology","Both","Electronics Hobbyist & Maker","₹3–6 LPA","High","Building IoT prototypes and robotics projects; competing in national science olympiads."),

        # ── School — Commerce & Management (extra) ────────────────
        ("School Student","Commerce & Management","Both","Social Media Marketing Intern","₹3–7 LPA","Exponential","Managing Instagram/YouTube content calendars and performance analytics for SME brands."),
        ("School Student","Commerce & Management","Both","E-Commerce Dropshipping Entrepreneur","₹Variable","Exponential","Running a D2C product business on Shopify or Amazon while in school."),
        ("School Student","Commerce & Management","Both","Financial Literacy Educator","₹4–8 LPA","High","Creating personal finance and stock market awareness content for young Indian audiences."),

        # ── School — Humanities & Social Sciences (extra) ─────────
        ("School Student","Humanities & Social Sciences","Both","Youth Activist & Policy Writer","₹3–7 LPA","Steady","Writing op-eds, policy briefs and participating in MUN conferences to build a public profile."),
        ("School Student","Humanities & Social Sciences","Both","Podcast Producer","₹3–8 LPA","Exponential","Recording, editing and distributing interview and narrative podcasts on history, culture or social issues."),
        ("School Student","Humanities & Social Sciences","Both","Language Tutor & Translator","₹3–7 LPA","Steady","Teaching regional or foreign languages online; doing subtitle and document translation gigs."),
    ]

    c.executemany(
        "INSERT INTO careers (level,stream,region,title,salary,outlook,duties) VALUES (?,?,?,?,?,?,?)",
        careers
    )
    conn.commit()
    return conn


DB = build_db()


@app.route('/api/courses')
def api_courses():
    level  = request.args.get('level', '')
    stream = request.args.get('stream', '')
    if level == 'School Student':
        data = SCHOOL_SUBJECTS.get(stream, {})
        return jsonify({"type": "subjects", "data": data})
    else:
        courses = COLLEGE_COURSES.get(stream, [])
        return jsonify({"type": "courses", "data": courses})


@app.route('/api/specs')
def api_specs():
    course_id = request.args.get('course_id', '')
    specs = SPECIALIZATIONS.get(course_id, [])
    return jsonify(specs)


@app.route('/api/colleges/locations')
def api_college_locations():
    c = DB.cursor()
    c.execute("SELECT DISTINCT location FROM colleges WHERE location IS NOT NULL AND location != '' ORDER BY location")
    locations = [r[0] for r in c.fetchall()]
    return jsonify(locations)


@app.route('/api/colleges/search')
def api_college_search():
    q = request.args.get('q', '').strip().lower()
    if not q or len(q) < 2:
        return jsonify([])
    c = DB.cursor()
    c.execute("""
        SELECT id, course_key, name, region, location, rank, fees, features FROM colleges
        WHERE LOWER(name) LIKE ?
           OR LOWER(location) LIKE ?
           OR LOWER(features) LIKE ?
           OR LOWER(rank) LIKE ?
        ORDER BY
            CASE WHEN LOWER(location) LIKE ? THEN 0
                 WHEN LOWER(name) LIKE ? THEN 1
                 ELSE 2 END,
            id
        LIMIT 5
    """, (f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%'))
    results = [dict(r) for r in c.fetchall()]
    annotate_colleges_with_exams(results)
    return jsonify(results)


@app.route('/browse')
@login_required
def browse():
    c = DB.cursor()
    region   = request.args.get('region', 'all')
    kind     = request.args.get('kind', 'colleges')
    q        = request.args.get('q', '').strip()

    if kind == 'careers':
        if q:
            like = f'%{q}%'
            c.execute("""SELECT DISTINCT level,stream,region,title,salary,outlook,duties FROM careers
                         WHERE LOWER(title) LIKE ? OR LOWER(duties) LIKE ? OR LOWER(salary) LIKE ?
                         ORDER BY title""", (like, like, like))
        elif region == 'India':
            c.execute("SELECT DISTINCT level,stream,region,title,salary,outlook,duties FROM careers WHERE region='India' ORDER BY title")
        elif region == 'Global':
            c.execute("SELECT DISTINCT level,stream,region,title,salary,outlook,duties FROM careers WHERE region='Abroad' ORDER BY title")
        else:
            c.execute("SELECT DISTINCT level,stream,region,title,salary,outlook,duties FROM careers ORDER BY title")
        items = [dict(r) for r in c.fetchall()]
        # deduplicate by title+region
        seen = set()
        deduped = []
        for item in items:
            key = (item['title'], item['region'])
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        items = deduped
    else:
        if q:
            like = f'%{q}%'
            c.execute("""SELECT * FROM colleges
                         WHERE LOWER(name) LIKE ? OR LOWER(location) LIKE ? OR LOWER(features) LIKE ?
                         ORDER BY region, id""", (like, like, like))
        elif region == 'India':
            c.execute("SELECT * FROM colleges WHERE region='India' ORDER BY id")
        elif region == 'Global':
            c.execute("SELECT * FROM colleges WHERE region='Abroad' ORDER BY id")
        else:
            c.execute("SELECT * FROM colleges ORDER BY region, id")
        all_rows = [dict(r) for r in c.fetchall()]
        # deduplicate by name+region
        seen = set()
        items = []
        for row in all_rows:
            key = (row['name'], row['region'])
            if key not in seen:
                seen.add(key)
                items.append(row)
    annotate_colleges_with_exams(items)

    c.execute("SELECT COUNT(*) FROM colleges")
    total_colleges = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM careers")
    total_careers = c.fetchone()[0]

    return render_template('browse.html',
        items=items,
        kind=kind,
        region=region,
        q=q,
        total_colleges=total_colleges,
        total_careers=total_careers,
        client_name=session.get('client_name', ''),
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        if not name or not email or '@' not in email:
            error = 'Please enter a valid name and email address.'
        else:
            save_client(name, email)
            session['client_name']  = name
            session['client_email'] = email
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    return render_template('index.html', client_name=session.get('client_name', ''))


PREP_TIPS = {
    "School Student": [
        {
            "category": "Entrance Exam Prep",
            "icon": "📝",
            "color": "purple",
            "tips": [
                "Start with NCERT textbooks — most entrance exams (JEE, NEET, CUET) are built directly on them.",
                "Solve the last 10 years' question papers under timed, exam-like conditions.",
                "Use the Pomodoro technique: 45 min focused study + 10 min break to stay sharp.",
                "Keep a dedicated 'Error Log' notebook — review every mistake weekly.",
                "Attempt at least one full-length mock test every week to build stamina.",
                "Make concise formula sheets and mind maps for quick last-minute revision.",
                "Rotate 2–3 subjects per day to avoid burnout and keep engagement high.",
            ],
        },
        {
            "category": "College Interview Tips",
            "icon": "🎤",
            "color": "blue",
            "tips": [
                "Research your target college — know its ranking, flagship programs, and recent achievements.",
                "Prepare a crisp 2-minute 'Tell me about yourself' answer covering academics and interests.",
                "Practice these common questions: 'Why this college?', 'Strengths & weaknesses?', 'Future goals?'",
                "Dress neatly and arrive 15 minutes early — punctuality signals professionalism.",
                "Maintain eye contact, sit upright, and speak at a steady, confident pace.",
                "It's fine to say 'I'm not sure, but I think…' — honesty beats bluffing.",
                "Prepare 2–3 thoughtful questions to ask the interviewer about the program.",
            ],
        },
        {
            "category": "Study Strategy",
            "icon": "📚",
            "color": "green",
            "tips": [
                "Build a weekly timetable — allocate time for all subjects including dedicated revision slots.",
                "Active recall (self-testing) is proven to be 3× more effective than re-reading notes.",
                "After each chapter, summarise it in your own words without looking at the book.",
                "Use spaced repetition: revisit topics after 1 day, 1 week, and 1 month.",
                "Form or join a study group — explaining concepts to others cements understanding.",
                "Protect 7–8 hours of sleep — memory consolidation happens while you sleep.",
                "Use app blockers during study hours to eliminate social media distractions.",
            ],
        },
        {
            "category": "Presentation & Viva",
            "icon": "🎯",
            "color": "rose",
            "tips": [
                "Structure every presentation: Hook → Main Content → Summary → Q&A.",
                "Practice speaking aloud — explain the slides, don't just read them.",
                "Each slide should carry one clear idea — max 5 bullet points, large legible font.",
                "Anticipate 3–5 questions and prepare short, confident answers in advance.",
                "Make eye contact with the audience rather than staring at the screen or your notes.",
                "Time yourself — finishing exactly on time shows preparation and respect.",
            ],
        },
        {
            "category": "Portfolio & Extracurriculars",
            "icon": "🏆",
            "color": "orange",
            "tips": [
                "Participate in Olympiads, science fairs, debate, or Model UN competitions.",
                "Build a small project tied to your stream — coding mini-app, science model, essay collection.",
                "Volunteer in community activities — it shows character beyond grades.",
                "Join school clubs (science, commerce, arts, coding) to signal genuine passion.",
                "Keep a folder of all certificates, awards, and achievements — digital and physical.",
                "Top colleges value consistent, meaningful extracurriculars as much as marks.",
            ],
        },
    ],
    "College Student": [
        {
            "category": "Campus Interview Prep",
            "icon": "💼",
            "color": "blue",
            "tips": [
                "Tailor your resume for each role — a one-size-fits-all resume rarely impresses.",
                "Research the company thoroughly: products, business model, recent news, and culture.",
                "Use the STAR method for behavioural questions: Situation → Task → Action → Result.",
                "For tech roles, practise LeetCode / HackerRank problems daily — consistency beats cramming.",
                "Prepare sharp answers for: 'Tell me about yourself', 'Why us?', 'Biggest failure?'",
                "Do mock interviews with peers or seniors — it dramatically reduces anxiety.",
                "Dress professionally — first impressions form in under 7 seconds.",
            ],
        },
        {
            "category": "Group Discussion (GD)",
            "icon": "🗣️",
            "color": "teal",
            "tips": [
                "Initiate the discussion if you're well-prepared on the topic — it makes a strong impression.",
                "Listen actively — acknowledge others' points before building on or countering them.",
                "Back your arguments with specific data, examples, or case studies.",
                "Aim for 3–4 quality contributions rather than dominating the conversation.",
                "If given the chance to summarise, do it — it demonstrates leadership.",
                "Disagree gracefully: 'I see your point; however…' rather than 'You're wrong'.",
                "Practise GDs with friends on current affairs, business cases, and social topics.",
            ],
        },
        {
            "category": "Micro Presentation",
            "icon": "🎯",
            "color": "purple",
            "tips": [
                "A micro-presentation is usually 3–5 minutes — plan every second deliberately.",
                "Open with a hook: a surprising statistic, bold claim, or one-line question.",
                "Use the 'What → So What → Now What' framework to structure your talk.",
                "Aim for 130–150 words per minute — clear and engaging without rushing.",
                "Use a maximum of 3 slides: Problem, Solution, Impact or Next Steps.",
                "End with one memorable takeaway or clear call to action.",
                "Always time yourself during practice — overrunning is a critical mistake in micro-presentations.",
            ],
        },
        {
            "category": "Resume & LinkedIn",
            "icon": "📄",
            "color": "green",
            "tips": [
                "Keep your resume to 1 page — recruiters spend an average of 7 seconds on the first scan.",
                "Lead with a 2-line professional summary: who you are, your top skill, and your goal.",
                "Quantify every achievement: 'Grew social reach by 40%' beats 'Managed social media'.",
                "Use strong action verbs: Led, Built, Designed, Analysed, Launched, Improved.",
                "Include a skills section with both technical tools and transferable soft skills.",
                "Keep your LinkedIn profile updated and connect actively with alumni and seniors.",
                "Request at least 3 meaningful recommendations from professors or internship managers.",
            ],
        },
        {
            "category": "Viva & Oral Exams",
            "icon": "🎓",
            "color": "indigo",
            "tips": [
                "Understand core concepts deeply — vivas test application and reasoning, not rote memory.",
                "Revise your own project or practical work thoroughly; examiners often start there.",
                "Prepare standard definitions for key terms in your subject.",
                "Structure your answers: Define → Explain → Give an example.",
                "If you don't know something, say what you do know and reason through it logically.",
                "Breathe before answering — a 2-second pause to think looks confident, not nervous.",
                "Professors respect intellectual honesty and clear logical thinking over guessed answers.",
            ],
        },
        {
            "category": "Internship Readiness",
            "icon": "🏢",
            "color": "orange",
            "tips": [
                "Build a portfolio: projects, case studies, or writing samples relevant to your field.",
                "Apply early — top internships open applications 4–6 months before the start date.",
                "Write a personalised cover letter for each application — never copy-paste.",
                "Cold-email professionals in your target field — many internships are never advertised.",
                "Follow up politely after applying — it signals initiative and genuine interest.",
                "Use LinkedIn for discovery, networking, and direct outreach to hiring managers.",
                "Prioritise learning and mentorship over stipend — the right experience opens bigger doors.",
            ],
        },
    ],
}

@app.route('/results', methods=['POST'])
@login_required
def results():
    level          = request.form.get('level', '')
    stream         = request.form.get('stream', '')
    course_key     = request.form.get('course_key', '')
    course_name    = request.form.get('course_name', '')
    specialization = request.form.get('specialization', '')
    subjects       = request.form.getlist('subjects')

    c = DB.cursor()

    if level == 'School Student':
        # Use the aspired course_key the student selected; fall back if needed
        lookup_key = course_key if course_key else SCHOOL_KEY_MAP.get(stream, 'school_commerce')
        if lookup_key in COURSE_FALLBACK:
            lookup_key = COURSE_FALLBACK[lookup_key]
        c.execute("SELECT * FROM colleges WHERE course_key=? AND region='India'",  (lookup_key,))
        india_colleges = [dict(r) for r in c.fetchall()]
        c.execute("SELECT * FROM colleges WHERE course_key=? AND region='Abroad'", (lookup_key,))
        abroad_colleges = [dict(r) for r in c.fetchall()]
        annotate_colleges_with_exams(india_colleges)
        annotate_colleges_with_exams(abroad_colleges)
        c.execute("SELECT * FROM careers WHERE level=? AND stream=?", (level, stream))
        careers = [dict(r) for r in c.fetchall()]
        india_careers  = []
        abroad_careers = []
    else:
        india_colleges  = []
        abroad_colleges = []
        careers         = []
        c.execute("SELECT * FROM careers WHERE level=? AND stream=? AND region='India'",  (level, stream))
        india_careers  = [dict(r) for r in c.fetchall()]
        c.execute("SELECT * FROM careers WHERE level=? AND stream=? AND region='Abroad'", (level, stream))
        abroad_careers = [dict(r) for r in c.fetchall()]

    prep_tips = PREP_TIPS.get(level, [])

    return render_template('results.html',
        level=level,
        stream=stream,
        stream_icon=STREAM_ICONS.get(stream, '🎓'),
        course_key=course_key,
        course_name=course_name,
        specialization=specialization,
        subjects=subjects,
        india_colleges=india_colleges,
        abroad_colleges=abroad_colleges,
        careers=careers,
        india_careers=india_careers,
        abroad_careers=abroad_careers,
        client_name=session.get('client_name', ''),
        prep_tips=prep_tips,
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
