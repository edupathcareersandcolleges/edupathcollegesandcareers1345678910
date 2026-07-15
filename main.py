import sqlite3

# =====================================================================
# 1. INDEPENDENT SQL DATABASE ARCHITECTURE ENGINE
# =====================================================================
def build_and_populate_database():
    # Setup an in-memory database instance to allow interactive runtime execution
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # --- SQL DDL LAYER: BUILD STRUCTURAL SYSTEM TABLES ---
    cursor.execute("DROP TABLE IF EXISTS careers;")
    cursor.execute("DROP TABLE IF EXISTS colleges;")
    cursor.execute("DROP TABLE IF EXISTS course_mappings;")
    
    # Create Table A: Master Educational Path Mappings
    cursor.execute('''
    CREATE TABLE course_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT NOT NULL,
        stream TEXT NOT NULL,
        course TEXT NOT NULL,
        subjects TEXT NOT NULL
    );''')
    
    # Create Table B: Curated Structural Directories for Colleges
    cursor.execute('''
    CREATE TABLE colleges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        name TEXT NOT NULL,
        region TEXT NOT NULL,
        rank TEXT,
        fees TEXT,
        features TEXT,
        FOREIGN KEY (course_id) REFERENCES course_mappings(id) ON DELETE CASCADE
    );''')
    
    # Create Table C: Top Strategic Corporate Career Blueprints
    cursor.execute('''
    CREATE TABLE careers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        title TEXT NOT NULL,
        salary TEXT,
        outlook TEXT,
        duties TEXT,
        FOREIGN KEY (course_id) REFERENCES course_mappings(id) ON DELETE CASCADE
    );''')

    # --- SQL DML LAYER: SEED FULL DATA DIRECTORIES ---
    
    # 1. Core Tracks Mapping Inserts
    courses_dataset = [
        # School Subsets (IDs 1-4)
        ('School Student', 'Commerce & Management', 'Higher Secondary (Accountancy, Business Studies & Economics)', 'Accountancy, Business Studies, Economics, Core Mathematics'),
        ('School Student', 'Engineering & Technology', 'Higher Secondary (Advanced STEM / PCM Track)', 'Physics, Chemistry, Advanced Mathematics, Computer Science'),
        ('School Student', 'Humanities & Social Sciences', 'Higher Secondary (Liberal Arts & Humanities Focus)', 'History, Political Science, Sociology, Psychology'),
        ('School Student', 'Medicine & Life Sciences', 'Higher Secondary (Pre-Medical / PCB Track)', 'Physics, Chemistry, Biology, Biotechnology'),
        # College Subsets (IDs 5-8)
        ('College Student', 'Commerce & Management', 'Bachelor of Commerce (B.Com Hons) in Accounting & Finance', 'Corporate Accounting, Financial Management, Audit, Advanced Taxation'),
        ('College Student', 'Engineering & Technology', 'B.Tech in Computer Science & Engineering (CSE)', 'Data Structures, Algorithms, Operating Systems, Computer Architecture'),
        ('College Student', 'Humanities & Social Sciences', 'Bachelor of Arts (B.A. Hons) in International Relations', 'Geopolitics, Political Theory, Global History, Foreign Policy Analysis'),
        ('College Student', 'Medicine & Life Sciences', 'Bachelor of Medicine, Bachelor of Surgery (MBBS)', 'Human Anatomy, Physiology, Biochemistry, Pathology, Pharmacology')
    ]
    cursor.executemany('INSERT INTO course_mappings (level, stream, course, subjects) VALUES (?,?,?,?)', courses_dataset)

    # 2. Comprehensive Global Colleges Directory Inserts (5 India, 5 Abroad per course)
    colleges_dataset = [
        # Course ID 1: School Commerce Track
        (1, 'The Doon School, Dehradun', 'India', '#1 National Boarding', '₹12-14 Lakhs/Yr', 'Elite alumni network, outstanding university placement cell.'),
        (1, 'La Martiniere for Boys, Kolkata', 'India', 'Top Tier Day School', '₹1.5-2 Lakhs/Yr', 'Legendary historical legacy, elite commerce and economics department.'),
        (1, 'DPS R.K. Puram, New Delhi', 'India', 'Top Academic Rank', '₹2-3 Lakhs/Yr', 'Consistently produces national toppers in corporate commerce boards.'),
        (1, 'St. Xavier’s Collegiate School, Kolkata', 'India', 'Top Historic Day School', '₹1-1.5 Lakhs/Yr', 'Rigorous academic tradition, excellent foundational accounting setup.'),
        (1, 'Campion School, Mumbai', 'India', '#1 Day School West', '₹2-3 Lakhs/Yr', 'Stellar management infrastructure and early leadership tracking.'),
        (1, 'Phillips Academy Andover', 'Abroad', '#1 US Boarding', '$65,000/Yr', 'Ivy League prep powerhouse, highly sophisticated global economics track.'),
        (1, 'Eton College, Windsor', 'Abroad', '#1 UK Historic', '£46,000/Yr', 'Educates global leaders, premier foundational financial history infrastructure.'),
        (1, 'Raffles Institution', 'Abroad', '#1 Singapore Public', '$15,000/Yr', 'Unrivaled Asian academic standards, fast-track pipeline to global finance hubs.'),
        (1, 'Charterhouse School', 'Abroad', 'Elite UK Boarding', '£44,000/Yr', 'World-famous economics and business operations foundational modules.'),
        (1, 'Trinity College School', 'Abroad', '#1 Canada Boarding', '$55,000/Yr', 'Exceptional global university preparation modules and leadership labs.'),

        # Course ID 2: School Engineering Track
        (2, 'DPS RK Puram, New Delhi', 'India', '#1 for Competitive Prep', '₹2-3 Lakhs/Yr', 'Stellar system for producing top-tier ranks in IIT-JEE and advanced science tracks.'),
        (2, 'DAV Boys Senior Secondary, Chennai', 'India', 'Top South Rank', '₹80,000/Yr', 'Known for producing hyper-focused mathematical and engineering minds.'),
        (2, 'FIITJEE Junior College, Hyderabad', 'India', 'Top Specialized Engineering', '₹3-4 Lakhs/Yr', 'Curriculum strictly optimized for competitive technical entrance exam matrices.'),
        (2, 'National Public School (NPS), Bangalore', 'India', 'Silicon Valley Pipeline', '₹1.5-2.5 Lakhs/Yr', 'Excellent computer science integration right into secondary schooling levels.'),
        (2, 'Bombay Scottish School, Mumbai', 'India', 'Top Academic ICSE', '₹1.5-2 Lakhs/Yr', 'Rigorous analytical tracking, highly advanced physics and mathematics labs.'),
        (2, 'Stuyvesant High School, New York', 'Abroad', '#1 US Public STEM', 'Free (Merit Exam)', 'Highly selective, foundational home to multiple Nobel laureates and tech founders.'),
        (2, 'Westminster School, London', 'Abroad', '#1 UK Academic', '£43,000/Yr', 'Unrivaled pipeline into Oxford and Cambridge engineering systems.'),
        (2, 'Thomas Jefferson High School for Science and Technology', 'Abroad', '#1 US STEM Academy', 'Free (Merit Exam)', 'State-of-the-art supercomputing and specialized aerospace labs available for students.'),
        (2, 'Hwa Chong Institution', 'Abroad', 'Elite Singapore STEM', '$12,000/Yr', 'Global powerhouse for math and physics Olympiad training circuits.'),
        (2, 'The Bronte College', 'Abroad', 'Top Canada Science', '$48,000/Yr', 'Accelerated AP/IB tracks tailored explicitly for international engineering admissions.'),

        # Course ID 3: School Humanities Track
        (3, 'Welham Girls’ School, Dehradun', 'India', '#1 Girls Boarding', '₹10-12 Lakhs/Yr', 'Produces exceptional liberal arts candidates and national policy thinkers.'),
        (3, 'Step by Step School, Noida', 'India', 'Top Modern Infrastructure', '₹3-4 Lakhs/Yr', 'Incredible psychological and political science laboratory modules for project work.'),
        (3, 'The Sanskaar Valley School, Bhopal', 'India', 'Top Central Region', '₹2.5-3.5 Lakhs/Yr', 'Exceptional theater, history debate, and public speaking infrastructure layout.'),
        (3, 'Sanskriti School, New Delhi', 'India', 'Civil Services Cohort', '₹1.5-2.5 Lakhs/Yr', 'Highly preferred by international diplomats and top-tier civil service families.'),
        (3, 'Loreto House, Kolkata', 'India', 'Top Historic Humanities', '₹1 Lakhs/Yr', 'Centuries-old reputation for building foundational paths in English and sociology.'),
        (3, 'Phillips Exeter Academy', 'Abroad', 'Elite US Harkness System', '$62,000/Yr', 'Uses the famous Harkness discussion method, ideal for advanced political study.'),
        (3, 'Harrow School, London', 'Abroad', 'Elite UK Tradition', '£45,000/Yr', 'Exceptional historical archives department, premier global leadership track.'),
        (3, 'United World College (UWC) South East Asia', 'Abroad', '#1 IB Global Profile', '$40,000/Yr', 'Hyper-diverse global cohort focusing strictly on international policy and human rights.'),
        (3, 'Upper Canada College', 'Abroad', 'Top Canada Liberal Arts', '$58,000/Yr', 'Stellar philosophy and global history tracks geared towards global university placement.'),
        (3, 'Ecole Nouvelle de la Suisse Romande', 'Abroad', 'Elite Switzerland Profile', 'CHF 75,000/Yr', 'Multilingual diplomatic baseline training located right in the heart of Europe.'),

        # Course ID 4: School Medicine Track
        (4, 'Sri Chaitanya Educational Institutions, Vijayawada', 'India', '#1 NEET Pipeline', '₹2.5-4 Lakhs/Yr', 'Produces absolute bulk share of top ranks in national pre-medical entry exams.'),
        (4, 'Allen Career Institute, Kota', 'India', 'World’s Largest Medical Academy', '₹1.5-3 Lakhs/Yr', 'The definitive global hub for competitive pre-medical biology and chemistry training.'),
        (4, 'Resonance, Kota', 'India', 'Top Competitive Hub', '₹1.5-2.5 Lakhs/Yr', 'Rigorous doubt-clearing structure with highly sophisticated medical mock analytics.'),
        (4, 'Modern School, Barakhamba Road, New Delhi', 'India', 'Top Legacy Infrastructure', '₹2-3 Lakhs/Yr', 'Exceptional biotechnology and advanced biochemistry infrastructure labs.'),
        (4, 'St. John’s High School, Chandigarh', 'India', 'Top North Academy', '₹1-1.5 Lakhs/Yr', 'Stellar record in advanced structural biological sciences study tracking.'),
        (4, 'Boston Latin School', 'Abroad', 'Historic US Pre-Med Academy', 'Free (Merit)', 'America’s oldest public school with unparalleled connections to Harvard Medical tracks.'),
        (4, 'St Paul’s School, London', 'Abroad', 'Elite UK Medical Track', '£42,000/Yr', 'Advanced organic chemistry laboratories that outpace many global universities.'),
        (4, 'Raffles Girls’ School', 'Abroad', 'Top Singapore Life Sciences', '$14,000/Yr', 'State-of-the-art genetic modeling equipment embedded directly into the school.'),
        (4, 'Columbia International College', 'Abroad', 'Top Canada Life Sciences', '$45,000/Yr', 'Accelerated pre-medical fast tracks linked to top North American systems.'),
        (4, 'The King’s School, Canterbury', 'Abroad', 'Elite UK Bio-Sciences', '£43,000/Yr', 'Strong institutional partnerships with leading European clinical research centers.'),

        # Course ID 5: College Commerce Track
        (5, 'Shri Ram College of Commerce (SRCC), Delhi', 'India', '#1 NIRF Commerce', '₹30,000/Yr', 'The gold standard for commerce in Asia. Perfect placements with top consulting/finance groups.'),
        (5, 'Loyola College, Chennai', 'India', 'Top Southern Hub', '₹45,000/Yr', 'Exceptional corporate relations division with brilliant accounting curriculum depth.'),
        (5, 'St. Xavier’s College, Mumbai', 'India', 'Elite Western Legacy', '₹25,000/Yr', 'Highly selective, incredible management alumni base dominating Dalal Street.'),
        (5, 'Christ University, Bangalore', 'India', 'Silicon Plateau Core', '₹2.5 Lakhs/Yr', 'Modern, industry-aligned syllabus focusing heavily on fintech and global certifications.'),
        (5, 'Anil Surendra Modi School of Commerce (NMIMS), Mumbai', 'India', 'Top Corporate Finance', '₹3.2 Lakhs/Yr', 'Rigorous corporate case-study methodology matching elite international business tracks.'),
        (5, 'London School of Economics (LSE)', 'Abroad', '#1 Global Accounting', '£28,000/Yr', 'Unrivaled global prestige, direct recruiting hub for Tier-1 Wall Street and London banks.'),
        (5, 'Wharton School, University of Pennsylvania', 'Abroad', '#1 US Business School', '$65,000/Yr', 'The absolute peak of financial education globally. Unrivaled multi-billion dollar alumni networks.'),
        (5, 'Stern School of Business, NYU', 'Abroad', '#2 Wall Street Pipeline', ' $62,000/Yr', 'Located blocks away from Wall Street, offering instant access to corporate year-round internships.'),
        (5, 'University of Cambridge (Judge Business)', 'Abroad', '#1 UK Elite traditional', '£35,000/Yr', 'Combines traditional high-finance research with deep mathematical economic logic.'),
        (5, 'Rotman School of Management, Toronto', 'Abroad', '#1 Canada Commerce', '$42,000/Yr', 'The premier gateway to the North American banking system and corporate financial centers.'),

        # Course ID 6: College Engineering Track
        (6, 'IIT Bombay', 'India', '#1 National Technical', '₹2.5 Lakhs/Yr', 'The ultimate dream destination for engineering. Massive incubation setups, elite global tech offers.'),
        (6, 'IIT Delhi', 'India', '#2 National Technical', '₹2.4 Lakhs/Yr', 'Elite computing systems infrastructure, highly competitive environment, located in primary startup hub.'),
        (6, 'IIT Madras', 'India', '#1 NIRF Engineering', '₹2.5 Lakhs/Yr', 'Houses India’s largest university research park, global leader in deep-tech tracking.'),
        (6, 'Indian Institute of Science (IISc), Bangalore', 'India', '#1 Research Index', '₹50,000/Yr', 'Focuses heavily on next-generation compiler design, quantum networks, and supercomputing systems.'),
        (6, 'BITS Pilani (Main Campus)', 'India', '#1 Private Engineering', '₹6.0 Lakhs/Yr', 'Zero attendance policy breeds intense engineering freedom and multi-million dollar tech startups.'),
        (6, 'Massachusetts Institute of Technology (MIT)', 'Abroad', '#1 Global Tech', '$64,000/Yr', 'The absolute epicenter of world computer science innovation and advanced AI architectures.'),
        (6, 'Stanford University', 'Abroad', '#2 Global Tech', '$66,000/Yr', 'The foundation engine of Silicon Valley, unparalleled access to venture funding systems.'),
        (6, 'Carnegie Mellon University (CMU)', 'Abroad', '#1 Software Engineering', '$60,000/Yr', 'World leader in specialized robotics, computational systems logic, and cybernetics.'),
        (6, 'University of California, Berkeley', 'Abroad', '#1 Public Global Tech', '$48,000/Yr', 'Pioneered foundational open-source technology, stellar research track in decentralized webs.'),
        (6, 'ETH Zurich', 'Abroad', '#1 Continental Europe', '$3,000/Yr', 'Incredible technological infrastructure at a fraction of the cost. Einstein’s alma mater.'),

        # Course ID 7: College Humanities Track
        (7, 'Lady Shri Ram College (LSR), New Delhi', 'India', '#1 Liberal Arts Focus', '₹20,000/Yr', 'Produces peak-level global diplomats, UN delegates, and international policy chiefs.'),
        (7, 'St. Stephen’s College, Delhi', 'India', 'Top National Legacy', '₹40,000/Yr', 'Elite historic cohort, highly intellectual debates, vast networks across the civil services.'),
        (7, 'Jawaharlal Nehru University (JNU), New Delhi', 'India', '#1 for Global Policy', '₹1,200/Yr', 'Unparalleled political discourse, incredible research output in international security studies.'),
        (7, 'Jadavpur University, Kolkata', 'India', 'Top Public Arts Hub', '₹3,000/Yr', 'Fierce socio-political history, world-renowned comparative international relations department.'),
        (7, 'Symbiosis School of International Studies, Pune', 'India', 'Top Private Policy Track', '₹3.5 Lakhs/Yr', 'Highly modern syllabus mapping global geopolitics, economic corridors, and simulated war-gaming.'),
        (7, 'Harvard University', 'Abroad', '#1 Ivy League Profile', '$68,000/Yr', 'Educates world presidents, direct control pipelines into global geopolitical strategy frameworks.'),
        (7, 'Sciences Po, Paris', 'Abroad', '#1 European Diplomacy', '€15,000/Yr', 'The definitive hub for European governance training, bilingual international relations tracks.'),
        (7, 'Georgetown University (Walsh School)', 'Abroad', '#1 Washington Pipeline', '$61,000/Yr', 'Located right in Washington D.C., directly linked with active state embassies and the Pentagon.'),
        (7, 'Graduate Institute of International Studies (IHEID), Geneva', 'Abroad', '#1 Global Security Hub', 'CHF 5,000/Yr', 'Directly integrated into the United Nations infrastructure in Geneva for immediate internships.'),
        (7, 'Australian National University (ANU)', 'Abroad', '#1 Asia-Pacific Strategy', '$38,000/Yr', 'The definitive authority on Asia-Pacific defense frameworks and maritime law policy.'),

        # Course ID 8: College Medicine Track
        (8, 'All India Institute of Medical Sciences (AIIMS), New Delhi', 'India', '#1 Medical National', '₹1,700 TOTAL FEES', 'The absolute peak of Indian medical education. Massive case exposure, ultimate clinical training.'),
        (8, 'Christian Medical College (CMC), Vellore', 'India', '#2 National Medical', '₹50,000/Yr', 'World-class community healthcare tracking systems and stellar diagnostic laboratories.'),
        (8, 'Armed Forces Medical College (AFMC), Pune', 'India', 'Elite Military Medicine', 'Free + Military Service', 'Incredible physical training alongside elite surgical residency systems.'),
        (8, 'Maulana Azad Medical College (MAMC), New Delhi', 'India', 'Top Clinical Caseload', '₹15,000/Yr', 'Unbelievable clinical diversity, handles thousands of out-patients every single day.'),
        (8, 'King George’s Medical University (KGMU), Lucknow', 'India', 'Top Legacy Medical', '₹60,000/Yr', 'Centuries-old legacy of surgical excellence and foundational clinical neural networks.'),
        (8, 'Harvard Medical School', 'Abroad', '#1 Global Medical', '$68,000/Yr', 'The frontier of worldwide surgical breakthroughs, computational biology, and elite residency tracks.'),
        (8, 'Johns Hopkins University School of Medicine', 'Abroad', '#1 Clinical Research', '$66,000/Yr', 'The worldwide gold standard for advanced neurosurgery systems and epidemiological models.'),
        (8, 'University of Oxford (Medical Sciences)', 'Abroad', '#1 UK Clinical Track', '£48,000/Yr', 'Brilliant translational medicine research frameworks combined with traditional tutor-led groups.'),
        (8, 'Karolinska Institutet', 'Abroad', '#1 Continental Europe', 'Free to €20k', 'The institution responsible for awarding the Nobel Prize in Medicine. Supreme research systems.'),
        (8, 'University of Toronto (Temerty Faculty)', 'Abroad', '#1 Canada Medical Hub', '$52,000/Yr', 'Unmatched infrastructure in stem-cell diagnostics and surgical robotic technologies.')
    ]
    cursor.executemany('INSERT INTO colleges (course_id, name, region, rank, fees, features) VALUES (?,?,?,?,?,?)', colleges_dataset)

    # 3. Comprehensive Corporate Strategic Careers Inserts (10 per course track)
    careers_dataset = [
        # Course 1: School Commerce Careers
        (1, 'Financial Portfolio Advisor', '₹8-15 LPA', 'High', 'Managing initial wealth metrics and preparing investment data maps.'),
        (1, 'Corporate Accountant Trainee', '₹6-10 LPA', 'Steady', 'Assisting corporate financial managers in calculating balance metrics.'),
        (1, 'Business Operations Assistant', '₹5-9 LPA', 'High', 'Reviewing product pipeline metrics and handling resource allocation logs.'),
        (1, 'Taxation Analyst', '₹7-12 LPA', 'Steady', 'Processing corporate tax filings and analyzing regulatory exemptions.'),
        (1, 'Commercial Credit Evaluator', '₹8-14 LPA', 'High', 'Evaluating banking risk parameters before commercial asset lending.'),
        (1, 'Stock Market Equity Associate', '₹10-18 LPA', 'Exponential', 'Tracking public equity markets and compiling stock behavior trackers.'),
        (1, 'Corporate Auditor', '₹7-13 LPA', 'Steady', 'Analyzing accounting integrity systems across major economic operations.'),
        (1, 'Supply Chain Logistics Analyst', '₹6-11 LPA', 'High', 'Optimizing cross-border inventory models for multinational commerce.'),
        (1, 'Retail Banking Branch Specialist', '₹5-8 LPA', 'Steady', 'Managing customer assets, capital accounts, and consumer micro-loans.'),
        (1, 'E-Commerce Business strategist', '₹9-16 LPA', 'High', 'Analyzing user transactional behavior to increase digital inventory sales.'),

        # Course 2: School Engineering Careers
        (2, 'Junior Python/Systems Developer', '₹6-12 LPA', 'High', 'Writing structural script wrappers and basic functional system blocks.'),
        (2, 'CAD Drafting Technical Engineer', '₹5-9 LPA', 'Steady', 'Building primary computer-aided industrial design frameworks for manufacturing.'),
        (2, 'QA Software Automation Tester', '₹6-10 LPA', 'High', 'Testing build instances for algorithmic exceptions and network faults.'),
        (2, 'Database Administration Assistant', '₹7-11 LPA', 'Steady', 'Writing clean SQL index structures and executing database recovery backups.'),
        (2, 'Network Infrastructure Technician', '₹5-9 LPA', 'Steady', 'Configuring routing protocols, local subnet layouts, and switch hardware.'),
        (2, 'Cybersecurity Operations Junior Analyst', '₹8-14 LPA', 'High', 'Monitoring threat logs for pattern anomalies across structural systems.'),
        (2, 'Web Applications Front-End Assistant', '₹6-11 LPA', 'High', 'Building clean client-facing code layouts using modern digital assets.'),
        (2, 'Embedded Systems Prototyper', '₹7-13 LPA', 'High', 'Programming microcontrollers and writing hardware-level sensor controls.'),
        (2, 'Data Analytics Junior Specialist', '₹8-15 LPA', 'Exponential', 'Compiling messy data files into clean dashboard visualization engines.'),
        (2, 'Cloud Storage Maintenance Associate', '₹7-12 LPA', 'High', 'Monitoring data pipelines and bucket access vectors across AWS architecture.'),

        # Course 3: School Humanities Careers
        (3, 'Public Content Strategy Lead', '₹6-10 LPA', 'High', 'Drafting long-form socio-political summaries for corporate outreach panels.'),
        (3, 'NGO Public Policy Coordinator', '₹5-8 LPA', 'Steady', 'Structuring ground-level community development plans and deployment files.'),
        (3, 'Media Communications Journalist', '₹6-12 LPA', 'Steady', 'Investigating domestic policy issues and compiling investigative reports.'),
        (3, 'Social Research Field Director', '₹5-9 LPA', 'Steady', 'Deploying regional demographic surveys to track public opinion changes.'),
        (3, 'Human Resources Staff Assistant', '₹6-10 LPA', 'High', 'Managing talent matching pipelines and organizational culture models.'),
        (3, 'Public Relations Liaison', '₹7-13 LPA', 'High', 'Constructing strategic messaging profiles to mitigate executive operational risks.'),
        (3, 'Digital Content Creator / Archivist', '₹5-11 LPA', 'Exponential', 'Managing historical asset catalogs and public cultural documentation networks.'),
        (3, 'Political Campaign Data Specialist', '₹8-15 LPA', 'High', 'Analyzing regional voting profiles to build demographic outreach systems.'),
        (3, 'Corporate Legal Document Compiler', '₹7-12 LPA', 'Steady', 'Reviewing compliance clauses and structural contractual requirements.'),
        (3, 'Museum Curation Assistant', '₹4-8 LPA', 'Steady', 'Preserving cultural artifacts and organizing public educational exhibitions.'),

        # Course 4: School Medicine Careers
        (4, 'Laboratory Diagnostics Associate', '₹5-9 LPA', 'Steady', 'Processing medical biological assays, blood logs, and tissue pathology files.'),
        (4, 'Clinical Research Assistant', '₹6-10 LPA', 'High', 'Tracking patient metric baselines for pharmaceutical development pipelines.'),
        (4, 'Health Information Technology Compiler', '₹5-8 LPA', 'Steady', 'Managing electronic medical records and secure healthcare database nodes.'),
        (4, 'Pharmaceutical Regulatory Consultant', '₹7-12 LPA', 'High', 'Reviewing drug safety dossiers for chemical compliance standards.'),
        (4, 'Bio-Medical Instrumentation Assistant', '₹6-11 LPA', 'Steady', 'Calibrating hospital equipment nodes including MRI systems and ventilators.'),
        (4, 'Public Healthcare Program Tracker', '₹5-9 LPA', 'High', 'Monitoring regional disease outbreaks and vaccination supply lines.'),
        (4, 'Dietetics & Nutrition Consultant', '₹6-10 LPA', 'High', 'Constructing clinical physiological diet plans for diagnostic recovery.'),
        (4, 'Genetic Counseling Associate', '₹8-13 LPA', 'Exponential', 'Analyzing familial chromosomal history to report inheritance risk factors.'),
        (4, 'Veterinary Clinical Technician', '₹5-8 LPA', 'Steady', 'Managing livestock medical plans and small-animal biological profiles.'),
        (4, 'Toxicology Screen Analyst', '₹7-12 LPA', 'Steady', 'Analyzing chemical environmental safety profiles and product ingredients.'),

        # Course 5: College Commerce Careers
        (5, 'Investment Banking Analyst', '$125k / ₹22 LPA', 'High', 'Executing structural financial models, M&A valuations, and capital raises.'),
        (5, 'Management Consultant (Big 3)', '$110k / ₹18 LPA', 'High', 'Restructuring global corporate supply lines and corporate strategy frameworks.'),
        (5, 'Chartered Accountant / CPA', '$90k / ₹14 LPA', 'Steady', 'Directing multi-million dollar corporate tax audits and forensic accounting layers.'),
        (5, 'Quantitative Hedge Fund Analyst', '$160k / ₹30 LPA', 'Exponential', 'Programming mathematical models to execute automated trading strategies.'),
        (5, 'Corporate Treasury Manager', '$105k / ₹16 LPA', 'Steady', 'Controlling cash flows, liquidity pools, and international currency risk layers.'),
        (5, 'Private Equity Associate', '$140k / ₹25 LPA', 'High', 'Sourcing mid-market corporate acquisitions and planning exit parameters.'),
        (5, 'Risk Management Specialist', '$98k / ₹13 LPA', 'High', 'Simulating economic market crash scenarios to insulate corporate equity fields.'),
        (5, 'Forensic Financial Investigator', '$115k / ₹16 LPA', 'High', 'Deconstructing complex money laundering structures and corporate fraud lines.'),
        (5, 'FinTech Product Owner', '$130k / ₹20 LPA', 'Exponential', 'Designing algorithmic payment architecture and digital banking pipelines.'),
        (5, 'Mergers & Acquisitions Director', '$200k / ₹40 LPA', 'High', 'Negotiating cross-border corporate takeovers and multi-billion asset sales.'),

        # Course 6: College Engineering Careers
        (6, 'AI / Machine Learning Architect', '$150k / ₹28 LPA', 'Exponential', 'Designing deep neural networks, custom LLM pipelines, and training algorithms.'),
        (6, 'Distributed Systems Engineer', '$135k / ₹22 LPA', 'High', 'Building highly parallel infrastructure loops and real-time database sync nodes.'),
        (6, 'Cloud DevOps Lead (AWS/Azure)', '$130k / ₹20 LPA', 'High', 'Constructing Kubernetes arrays, automated CI/CD pipelines, and zero-downtime systems.'),
        (6, 'Cybersecurity Zero-Trust Specialist', '$140k / ₹24 LPA', 'High', 'Engineering cryptographic core layers and hardening containerized runtime systems.'),
        (6, 'Blockchain Protocol Developer', '$138k / ₹21 LPA', 'Steady', 'Writing optimized EVM smart contracts and consensus layer protocols.'),
        (6, 'Quantitative Developer', '$180k / ₹35 LPA', 'Exponential', 'Translating high-frequency financial options algorithms into C++ execution models.'),
        (6, 'Data Infrastructure Engineer', '$125k / ₹18 LPA', 'High', 'Managing multi-petabyte real-time streaming data buses using Kafka setups.'),
        (6, 'Full-Stack Software Architect', '$142k / ₹22 LPA', 'High', 'Overseeing complete structural framework design across backends and client layers.'),
        (6, 'Autonomous Robotics Engineer', '$132k / ₹19 LPA', 'High', 'Programming spatial awareness, SLAM loops, and sensor fusion processing software.'),
        (6, 'Quantum Software Researcher', '$165k / ₹32 LPA', 'Emerging', 'Writing non-Boolean algorithms for experimental cryogenic processing modules.'),

        # Course 7: College Humanities Careers
        (7, 'Foreign Services Diplomat', 'Varies / Group A', 'Steady', 'Negotiating international bilateral trade deals and protecting embassy parameters.'),
        (7, 'Geopolitical Risk Consultant', '$115k / ₹16 LPA', 'High', 'Advising multinationals on war zones, structural resource blockades, and political coups.'),
        (7, 'United Nations Policy Advisor', '$95k / ₹12 LPA', 'Steady', 'Drafting international human rights documentation and directing refugee relief projects.'),
        (7, 'Intelligence Analyst (CIA/RAW)', 'Govt Scale', 'High', 'Deconstructing satellite imagery, encrypted communications logs, and state data feeds.'),
        (7, 'International Arbitration Attorney', '$160k / ₹26 LPA', 'High', 'Litigating multi-billion dollar legal battles between corporations and sovereign states.'),
        (7, 'Global Think-Tank Director', '$120k / ₹18 LPA', 'Steady', 'Directing economic policy monographs and whitepapers on global security shifts.'),
        (7, 'Foreign Intelligence Journalist', '$85k / ₹11 LPA', 'Steady', 'Reporting live from active military conflicts and global treaty conventions.'),
        (7, 'Corporate Sustainability Lead', '$110k / ₹15 LPA', 'High', 'Aligning supply networks with cross-border ESG and carbon credit markets.'),
        (7, 'International Trade Negotiator', '$130k / ₹20 LPA', 'High', 'Structuring tariff modifications and trade treaty protocols for federal commerce.'),
        (7, 'Conflict Resolution Mediator', '$105k / ₹14 LPA', 'Steady', 'Brokering territorial peace matrices and cross-border structural resource partitions.'),

        # Course 8: College Medicine Careers
        (8, 'Cardiothoracic Surgeon', '$450k / ₹45 LPA', 'High', 'Executing open-heart vascular configurations and coronary bypass operations.'),
        (8, 'Interventional Neurosurgeon', '$580k / ₹60 LPA', 'Exponential', 'Operating on cerebral aneurysms and micro-vascular neural tumor systems.'),
        (8, 'Diagnostic Radiology Specialist', '$390k / ₹35 LPA', 'High', 'Interpreting complex MRI, CT, and PET molecular structural scans.'),
        (8, 'Clinical Oncologist', '$320k / ₹28 LPA', 'High', 'Designing complex immunotherapeutic oncology regimens and precision targeted radiation.'),
        (8, 'Orthopedic Trauma Surgeon', '$410k / ₹40 LPA', 'Steady', 'Reconstructing structural skeletal fields and complex articular joint systems.'),
        (8, 'Epidemiology Field Director', '$140k / ₹22 LPA', 'High', 'Modeling structural viral transmission systems and controlling infectious disease nodes.'),
        (8, 'Biomedical Gene Therapist', '$180k / ₹26 LPA', 'Exponential', 'Using CRISPR gene-editing tools to eliminate congenital cellular anomalies.'),
        (8, 'Chief Medical Officer (CMO)', '$280k / ₹36 LPA', 'High', 'Directing absolute clinical operations and healthcare resource parameters for hospital systems.'),
        (8, 'Pediatric Cardiology Specialist', '$360k / ₹32 LPA', 'High', 'Treating congenital heart infrastructure defects within neonatal patient groups.'),
        (8, 'Aerospace Medical Officer', '$190k / ₹25 LPA', 'Emerging', 'Insulating astronaut biological health metrics against long-duration space flight stress.')
    ]
    cursor.executemany('INSERT INTO careers (course_id, title, salary, outlook, duties) VALUES (?,?,?,?,?)', careers_dataset)
    
    conn.commit()
    return conn

# =====================================================================
# 2. RUNTIME GRAPHICAL USER INTERFACE SIMULATION
# =====================================================================
def start_portal_runtime():
    # Build database tables using pure SQL behind the scenes
    db_connection = build_and_populate_database()
    sql_executor = db_connection.cursor()
    
    print("=" * 80)
    print("SMART CAREER & COLLEGE GUIDANCE PORTAL".center(80))
    print("=" * 80)
    
    # -------------------------------------------------------------
    # INPUT INTERFACE STEP 1: Academic Profile Level Selection
    # -------------------------------------------------------------
    print("\n[STEP 1]: Choose your current core educational baseline classification:")
    print(" 1. School Student")
    print(" 2. College Student")
    user_tier_input = input("Enter option number (1-2): ").strip()
    target_level = "School Student" if user_tier_input == "1" else "College Student"
    
    # -------------------------------------------------------------
    # INPUT INTERFACE STEP 2: Professional Stream Category Filter
    # -------------------------------------------------------------
    streams_directory = {
        "1": "Commerce & Management",
        "2": "Engineering & Technology",
        "3": "Humanities & Social Sciences",
        "4": "Medicine & Life Sciences"
    }
    print("\n[STEP 2]: Select your target professional stream framework:")
    for key, value in streams_directory.items():
        print(f" {key}. {value}")
    user_stream_input = input("Enter track option number (1-4): ").strip()
    target_stream = streams_directory.get(user_stream_input, "Engineering & Technology")
    
    # -------------------------------------------------------------
    # INPUT INTERFACE STEP 3: Automated SQL Execution & Verification
    # -------------------------------------------------------------
    # SQL Query acts on runtime variables passed inside parameters tuple
    sql_executor.execute("SELECT id, course, subjects FROM course_mappings WHERE level=? AND stream=?", (target_level, target_stream))
    matched_db_tracks = sql_executor.fetchall()
    
    if not matched_db_tracks:
        print("\n[System Alert]: Verification error mapping background tracks. Aborting query.")
        return

    # Automatically identify specific curriculum structure from matching entry
    active_course_id = matched_db_tracks[0][0]
    active_course_name = matched_db_tracks[0][1]
    mapped_subjects = matched_db_tracks[0][2]
    
    print(f"\n[STEP 3]: Auto-Verified Track Definition Confirmation:")
    print(f" » Academic Track: {active_course_name}")
    print(f" » Core Background Subjects Checked: [{mapped_subjects}]")
    
    # -------------------------------------------------------------
    # INPUT INTERFACE STEP 4: Geographic Target Matrix
    # -------------------------------------------------------------
    print("\n[STEP 4]: Specify geographical framework limits for future studies:")
    print(" 1. India")
    print(" 2. Abroad")
    user_geo_input = input("Enter region selection option (1-2): ").strip()
    target_destination = "India" if user_geo_input == "1" else "Abroad"

    # =====================================================================
    # 3. DYNAMIC METRIC GENERATION ENGINE (SQL COMBINED EXTRACTIONS)
    # =====================================================================
    print("\n" + "#" * 80)
    print(" PORTAL SYSTEMS DATA VERIFICATION INTERACTIVE REPORT ".center(80, "#"))
    print("#" * 80)
    print(f" » Profile Track Core:   {target_level.upper()} // {target_stream.upper()}")
    print(f" » Target Focus Route:   {active_course_name}")
    print(f" » Geographic Pipeline:  {target_destination.upper()}")
    print("#" * 80)

    # SQL Fetch A: Identify 5 Target Colleges corresponding to the profile criteria
    sql_executor.execute("SELECT name, rank, fees, features FROM colleges WHERE course_id=? AND region=?", (active_course_id, target_destination))
    college_results = sql_executor.fetchall()
    
    print(f"\n🏆 TOP RECOMMENDED ACADEMIC INSTITUTIONS FOR HIGHER ED IN [{target_destination.upper()}] 🏆")
    print("-" * 80)
    if college_results:
        for index, row in enumerate(college_results, 1):
            print(f"{index}. 🏛️  University: {row[0]}")
            print(f"    Target Placement/Global Rank: {row[1]} | Annual Budget: {row[2]}")
            print(f"    Strategic Distinct Highlights: {row[3]}\n")
    else:
        print("    No dynamic listing matches exist in database directory tables for this specific index.\n")

    # SQL Fetch B: Identify all 10 detailed Corporate Careers mapped to the profile
    sql_executor.execute("SELECT title, salary, outlook, duties FROM careers WHERE course_id=?", (active_course_id,))
    career_results = sql_executor.fetchall()
    
    print(f"🚀 TOP 10 HIGH-VALUE CAREER BLUEPRINTS FOR THIS PROFESSIONAL DOMAIN 🚀")
    print("-" * 80)
    if career_results:
        for index, row in enumerate(career_results, 1):
            print(f"{index}. 💼 Structural Title: {row[0]}")
            print(f"    Compensation Package Baseline: {row[1]} | Market Scale Outlook: {row[2]}")
            print(f"    Core System Operational Duties: {row[3]}\n")
    else:
        print("    No structural career tracks mapped to this profile index directory point.\n")
        
    print("#" * 80)

# Fire up the combined master framework application engine
if __name__ == "__main__":
    start_portal_runtime()